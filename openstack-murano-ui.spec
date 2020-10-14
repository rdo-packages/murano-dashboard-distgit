%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%global pypi_name murano-dashboard
%global mod_name muranodashboard
%global with_doc 1

%global common_desc \
Murano Dashboard is an extension for OpenStack Dashboard that provides a UI \
for Murano. With murano-dashboard, a user is able to easily manage and control \
an application catalog, running applications and created environments alongside \
with all other OpenStack resources.

Name:           openstack-murano-ui
Version:        10.0.0
Release:        1%{?dist}
Summary:        The UI component for the OpenStack murano service
Group:          Applications/Communications
License:        ASL 2.0
URL:            https://github.com/openstack/%{pypi_name}
Source0:        https://tarballs.openstack.org/%{pypi_name}/%{pypi_name}-%{upstream_version}.tar.gz
#

BuildArch:      noarch

BuildRequires:  gettext
BuildRequires:  git
BuildRequires:  openstack-dashboard
BuildRequires:  python3-castellan
BuildRequires:  python3-devel
BuildRequires:  python3-django-formtools
BuildRequires:  python3-django-nose
BuildRequires:  python3-mock
BuildRequires:  python3-mox3
BuildRequires:  python3-muranoclient
BuildRequires:  python3-nose
BuildRequires:  python3-oslo-config >= 2:5.1.0
BuildRequires:  python3-pbr >= 2.0.0
BuildRequires:  python3-setuptools
BuildRequires:  python3-testtools
BuildRequires:  python3-yaql >= 1.1.3
BuildRequires:  openstack-macros
BuildRequires:  python3-beautifulsoup4
BuildRequires:  python3-semantic_version

Requires:       openstack-dashboard >= 18.3.0
Requires:       python3-castellan >= 0.18.0
Requires:       python3-django-formtools
# django-floppyforms is not packaged in Fedora yet.
#Requires:       python3-django-floppyforms
Requires:       python3-iso8601 >= 0.1.11
Requires:       python3-muranoclient >= 0.8.2
Requires:       python3-oslo-log >= 3.36.0
Requires:       python3-pbr
Requires:       python3-yaql >= 1.1.3
Requires:       python3-pytz
Requires:       python3-PyYAML >= 3.10
Requires:       python3-beautifulsoup4
Requires:       python3-semantic_version

%description
Murano Dashboard
Sytem package - murano-dashboard
Python package - murano-dashboard
%{common_desc}

%if 0%{?with_doc}
%package doc
Summary:        Documentation for OpenStack murano dashboard
BuildRequires:  python3-sphinx
BuildRequires:  python3-openstackdocstheme
BuildRequires:  python3-reno

%description doc
%{common_desc}

This package contains the documentation.
%endif

%prep
%autosetup -n %{pypi_name}-%{upstream_version} -S git
# Let RPM handle the dependencies
%py_req_cleanup

# disable warning-is-error, this project has intersphinx in docs
# so some warnings are generated in network isolated build environment
# as koji
sed -i 's/^warning-is-error.*/warning-is-error = 0/g' setup.cfg

%build
%{py3_build}
# Generate i18n files
pushd build/lib/%{mod_name}
django-admin compilemessages
popd

%if 0%{?with_doc}
# generate html docs
export OSLO_PACKAGE_VERSION=%{upstream_version}
sphinx-build -b html doc/source doc/build/html
# remove the sphinx-build leftovers
rm -rf doc/build/html/.{doctrees,buildinfo}
%endif

%install
%{py3_install}
mkdir -p %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/enabled
mkdir -p %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/local_settings.d
mkdir -p %{buildroot}/var/cache/murano-dashboard
# Enable Horizon plugin for murano-dashboard
cp %{_builddir}/%{pypi_name}-%{upstream_version}/muranodashboard/local/local_settings.d/_50_murano.py %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/local_settings.d/
cp %{_builddir}/%{pypi_name}-%{upstream_version}/muranodashboard/local/enabled/_*.py %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/enabled/

%check
export PYTHONPATH="%{_datadir}/openstack-dashboard:%{python3_sitearch}:%{python3_sitelib}:%{buildroot}%{python3_sitelib}"
# (TODO) Re-enable unit tests once package for openstack/heat-dashboard is included in RDO and https://review.openstack.org/#/c/527955/
# is merged
%{__python3} manage.py test muranodashboard --settings=muranodashboard.tests.settings||:

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
%{python3_sitelib}/muranodashboard
%{python3_sitelib}/murano_dashboard*.egg-info
%{_datadir}/openstack-dashboard/openstack_dashboard/local/local_settings.d/*
%{_datadir}/openstack-dashboard/openstack_dashboard/local/enabled/*
%dir %attr(755, apache, apache) /var/cache/murano-dashboard

%if 0%{?with_doc}
%files doc
%license LICENSE
%doc doc/build/html
%endif

%changelog
* Wed Oct 14 2020 RDO <dev@lists.rdoproject.org> 10.0.0-1
- Update to 10.0.0

* Thu Sep 24 2020 RDO <dev@lists.rdoproject.org> 10.0.0-0.1.0rc1
- Update to 10.0.0.0rc1

