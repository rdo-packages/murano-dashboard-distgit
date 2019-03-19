# Macros for py2/py3 compatibility
%if 0%{?fedora} || 0%{?rhel} > 7
%global pyver %{python3_pkgversion}
%else
%global pyver 2
%endif
%global pyver_bin python%{pyver}
%global pyver_sitelib %python%{pyver}_sitelib
%global pyver_sitearch %python%{pyver}_sitearch
%global pyver_install %py%{pyver}_install
%global pyver_build %py%{pyver}_build
# End of macros for py2/py3 compatibility
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%global pypi_name murano-dashboard
%global mod_name muranodashboard

%global common_desc \
Murano Dashboard is an extension for OpenStack Dashboard that provides a UI \
for Murano. With murano-dashboard, a user is able to easily manage and control \
an application catalog, running applications and created environments alongside \
with all other OpenStack resources.

Name:           openstack-murano-ui
Version:        XXX
Release:        XXX
Summary:        The UI component for the OpenStack murano service
Group:          Applications/Communications
License:        ASL 2.0
URL:            https://github.com/openstack/%{pypi_name}
Source0:        https://tarballs.openstack.org/%{pypi_name}/%{pypi_name}-%{upstream_version}.tar.gz
BuildArch:      noarch

BuildRequires:  gettext
BuildRequires:  git
BuildRequires:  openstack-dashboard
BuildRequires:  python%{pyver}-castellan
BuildRequires:  python%{pyver}-devel
BuildRequires:  python%{pyver}-django-formtools
BuildRequires:  python%{pyver}-django-nose
BuildRequires:  python%{pyver}-mock
BuildRequires:  python%{pyver}-mox3
BuildRequires:  python%{pyver}-muranoclient
BuildRequires:  python%{pyver}-nose
BuildRequires:  python%{pyver}-oslo-config >= 2:5.1.0
BuildRequires:  python%{pyver}-pbr >= 2.0.0
BuildRequires:  python%{pyver}-setuptools
BuildRequires:  python%{pyver}-testtools
BuildRequires:  python%{pyver}-yaql >= 1.1.3
BuildRequires:  openstack-macros
# Handle python2 exception
%if %{pyver} == 2
BuildRequires:  python-beautifulsoup4
BuildRequires:  python-semantic_version
%else
BuildRequires:  python%{pyver}-beautifulsoup4
BuildRequires:  python%{pyver}-semantic_version
%endif

Requires:       openstack-dashboard >= 15.0.0
Requires:       python%{pyver}-babel >= 2.3.4
Requires:       python%{pyver}-castellan >= 0.18.0
Requires:       python%{pyver}-django >= 1.8
Requires:       python%{pyver}-django-babel
Requires:       python%{pyver}-django-formtools
# django-floppyforms is not packaged in Fedora yet.
#Requires:       python%{pyver}-django-floppyforms
Requires:       python%{pyver}-iso8601 >= 0.1.11
Requires:       python%{pyver}-muranoclient >= 0.8.2
Requires:       python%{pyver}-oslo-log >= 3.36.0
Requires:       python%{pyver}-pbr
Requires:       python%{pyver}-six >= 1.10.0
Requires:       python%{pyver}-yaql >= 1.1.3
Requires:       python%{pyver}-pytz
# Handle python2 exception
%if %{pyver} == 2
Requires:       PyYAML >= 3.10
Requires:       python-beautifulsoup4
Requires:       python-semantic_version
%else
Requires:       python%{pyver}-PyYAML >= 3.10
Requires:       python%{pyver}-beautifulsoup4
Requires:       python%{pyver}-semantic_version
%endif

%description
Murano Dashboard
Sytem package - murano-dashboard
Python package - murano-dashboard
%{common_desc}

%package doc
Summary:        Documentation for OpenStack murano dashboard
BuildRequires:  python%{pyver}-sphinx
BuildRequires:  python%{pyver}-openstackdocstheme
BuildRequires:  python%{pyver}-reno

%description doc
%{common_desc}

This package contains the documentation.

%prep
%autosetup -n %{pypi_name}-%{upstream_version} -S git
# Let RPM handle the dependencies
%py_req_cleanup

# disable warning-is-error, this project has intersphinx in docs
# so some warnings are generated in network isolated build environment
# as koji
sed -i 's/^warning-is-error.*/warning-is-error = 0/g' setup.cfg

%build
%{pyver_build}
# Generate i18n files
pushd build/lib/%{mod_name}
django-admin compilemessages
popd
# generate html docs
export OSLO_PACKAGE_VERSION=%{upstream_version}
%{pyver_bin} setup.py build_sphinx -b html
# remove the sphinx-build-%{pyver} leftovers
rm -rf doc/build/html/.{doctrees,buildinfo}

%install
%{pyver_install}
mkdir -p %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/enabled
mkdir -p %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/local_settings.d
mkdir -p %{buildroot}/var/cache/murano-dashboard
# Enable Horizon plugin for murano-dashboard
cp %{_builddir}/%{pypi_name}-%{upstream_version}/muranodashboard/local/local_settings.d/_50_murano.py %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/local_settings.d/
cp %{_builddir}/%{pypi_name}-%{upstream_version}/muranodashboard/local/enabled/_*.py %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/enabled/

%check
export PYTHONPATH="%{_datadir}/openstack-dashboard:%{pyver_sitearch}:%{pyver_sitelib}:%{buildroot}%{pyver_sitelib}"
# (TODO) Re-enable unit tests once package for openstack/heat-dashboard is included in RDO and https://review.openstack.org/#/c/527955/
# is merged
%{pyver_bin} manage.py test muranodashboard --settings=muranodashboard.tests.settings||:

%post
HORIZON_SETTINGS='/etc/openstack-dashboard/local_settings'
if grep -Eq '^METADATA_CACHE_DIR=' $HORIZON_SETTINGS; then
  sed -i '/^METADATA_CACHE_DIR=/{s#.*#METADATA_CACHE_DIR="/var/cache/murano-dashboard"#}' $HORIZON_SETTINGS
else
  sed -i '$aMETADATA_CACHE_DIR="/var/cache/murano-dashboard"' $HORIZON_SETTINGS
fi
%systemd_postun_with_restart httpd.service

%postun
%systemd_postun_with_restart httpd.service

%files
%license LICENSE
%doc README.rst
%{pyver_sitelib}/muranodashboard
%{pyver_sitelib}/murano_dashboard*.egg-info
%{_datadir}/openstack-dashboard/openstack_dashboard/local/local_settings.d/*
%{_datadir}/openstack-dashboard/openstack_dashboard/local/enabled/*
%dir %attr(755, apache, apache) /var/cache/murano-dashboard

%files doc
%license LICENSE
%doc doc/build/html

%changelog
