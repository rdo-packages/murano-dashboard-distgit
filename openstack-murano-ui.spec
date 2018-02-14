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
BuildRequires:  gettext
BuildRequires:  git
BuildRequires:  openstack-dashboard
BuildRequires:  python2-beautifulsoup4
BuildRequires:  python2-castellan
BuildRequires:  python2-devel
BuildRequires:  python2-django-formtools
BuildRequires:  python2-django-nose
BuildRequires:  python2-mock
BuildRequires:  python2-mox3
BuildRequires:  python2-muranoclient
BuildRequires:  python2-nose
BuildRequires:  python-openstack-nose-plugin
BuildRequires:  python2-oslo-config >= 2:5.1.0
BuildRequires:  python2-pbr >= 1.6
BuildRequires:  python2-semantic-version
BuildRequires:  python2-setuptools
BuildRequires:  python2-testtools
BuildRequires:  python2-yaql >= 1.1.3
BuildRequires:  openstack-macros
Requires:       openstack-dashboard
Requires:       PyYAML >= 3.10
Requires:       python2-babel >= 2.3.4
Requires:       python2-beautifulsoup4
Requires:       python2-castellan >= 0.16.0
Requires:       python2-django >= 1.8
Requires:       python2-django-babel
Requires:       python2-django-formtools
Requires:       python2-iso8601 >= 0.1.11
Requires:       python2-muranoclient >= 0.8.2
Requires:       python2-oslo-log >= 3.36.0
Requires:       python2-pbr
Requires:       python2-semantic-version
Requires:       python2-six >= 1.10.0
Requires:       python2-yaql >= 1.1.3
Requires:       pytz
BuildArch:      noarch

%description
Murano Dashboard
Sytem package - murano-dashboard
Python package - murano-dashboard
%{common_desc}

%package doc
Summary:        Documentation for OpenStack murano dashboard
BuildRequires:  python2-sphinx
BuildRequires:  python2-openstackdocstheme
BuildRequires:  python2-reno

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
%py2_build
# Generate i18n files
pushd build/lib/%{mod_name}
django-admin compilemessages
popd
# generate html docs
export OSLO_PACKAGE_VERSION=%{upstream_version}
%{__python2} setup.py build_sphinx -b html
# remove the sphinx-build leftovers
rm -rf doc/build/html/.{doctrees,buildinfo}

%install
%py2_install
mkdir -p %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/enabled
mkdir -p %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/local_settings.d
mkdir -p %{buildroot}/var/cache/murano-dashboard
# Enable Horizon plugin for murano-dashboard
cp %{_builddir}/%{pypi_name}-%{upstream_version}/muranodashboard/local/local_settings.d/_50_murano.py %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/local_settings.d/
cp %{_builddir}/%{pypi_name}-%{upstream_version}/muranodashboard/local/enabled/_*.py %{buildroot}%{_datadir}/openstack-dashboard/openstack_dashboard/local/enabled/

%check
export PYTHONPATH="%{_datadir}/openstack-dashboard:%{python2_sitearch}:%{python2_sitelib}:%{buildroot}%{python2_sitelib}"
# (TODO) Re-enable unit tests once package for openstack/heat-dashboard is included in RDO and https://review.openstack.org/#/c/527955/
# is merged
%{__python2} manage.py test muranodashboard --settings=muranodashboard.tests.settings||:

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
%{python2_sitelib}/muranodashboard
%{python2_sitelib}/murano_dashboard*.egg-info
%{_datadir}/openstack-dashboard/openstack_dashboard/local/local_settings.d/*
%{_datadir}/openstack-dashboard/openstack_dashboard/local/enabled/*
%dir %attr(755, apache, apache) /var/cache/murano-dashboard

%files doc
%license LICENSE
%doc doc/build/html

%changelog
