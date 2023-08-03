%{!?sources_gpg: %{!?dlrn:%global sources_gpg 1} }
%global sources_gpg_sign 0x2426b928085a020d8a90d0d879ab7008d0896c8a
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
# we are excluding some BRs from automatic generator
%global excluded_brs doc8 bandit pre-commit hacking flake8-import-order bashate nodeenv
# Exclude sphinx from BRs if docs are disabled
%if ! 0%{?with_doc}
%global excluded_brs %{excluded_brs} sphinx openstackdocstheme
%endif
%global pypi_name murano-dashboard
%global mod_name muranodashboard
%global with_doc 1

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
License:        Apache-2.0
URL:            https://github.com/openstack/%{pypi_name}
Source0:        https://tarballs.openstack.org/%{pypi_name}/%{pypi_name}-%{upstream_version}.tar.gz
# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
Source101:        https://tarballs.openstack.org/%{pypi_name}/%{pypi_name}-%{upstream_version}.tar.gz.asc
Source102:        https://releases.openstack.org/_static/%{sources_gpg_sign}.txt
%endif
BuildArch:      noarch

# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
BuildRequires:  /usr/bin/gpgv2
%endif

BuildRequires:  gettext
BuildRequires:  git-core
BuildRequires:  openstack-dashboard
BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  openstack-macros
Requires:       openstack-dashboard >= 18.3.1

%description
Murano Dashboard
Sytem package - murano-dashboard
Python package - murano-dashboard
%{common_desc}

%if 0%{?with_doc}
%package doc
Summary:        Documentation for OpenStack murano dashboard
%description doc
%{common_desc}

This package contains the documentation.
%endif

%prep
# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
%{gpgverify}  --keyring=%{SOURCE102} --signature=%{SOURCE101} --data=%{SOURCE0}
%endif
%autosetup -n %{pypi_name}-%{upstream_version} -S git

sed -i /^[[:space:]]*-c{env:.*_CONSTRAINTS_FILE.*/d tox.ini
sed -i "s/^deps = -c{env:.*_CONSTRAINTS_FILE.*/deps =/" tox.ini
sed -i /^minversion.*/d tox.ini
sed -i /^requires.*virtualenv.*/d tox.ini

sed -i /.*tarballs.openstack.org/d tox.ini

# Exclude some bad-known BRs
for pkg in %{excluded_brs}; do
  for reqfile in doc/requirements.txt test-requirements.txt; do
    if [ -f $reqfile ]; then
      sed -i /^${pkg}.*/d $reqfile
    fi
  done
done

# Automatic BR generation
%generate_buildrequires
%if 0%{?with_doc}
  %pyproject_buildrequires -t -e %{default_toxenv},docs
%else
  %pyproject_buildrequires -t -e %{default_toxenv}
%endif

%build
%pyproject_wheel


%if 0%{?with_doc}
# generate html docs
export OSLO_PACKAGE_VERSION=%{upstream_version}
%tox -e docs
# remove the sphinx-build leftovers
rm -rf doc/build/html/.{doctrees,buildinfo}
%endif

%install
%pyproject_install

# Generate i18n files
pushd %{buildroot}/%{python3_sitelib}/%{mod_name}
django-admin compilemessages
popd

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
%{python3_sitelib}/murano_dashboard*.dist-info
%{_datadir}/openstack-dashboard/openstack_dashboard/local/local_settings.d/*
%{_datadir}/openstack-dashboard/openstack_dashboard/local/enabled/*
%dir %attr(755, apache, apache) /var/cache/murano-dashboard

%if 0%{?with_doc}
%files doc
%license LICENSE
%doc doc/build/html
%endif

%changelog
# REMOVEME: error caused by commit https://opendev.org/openstack/murano-dashboard/commit/2c1c88a708c348728a5941cc91b538ad68658287
