%{!?scl:%global pkg_name %{name}}

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

%global         django_version  1.5.5
%global         south_version   0.8.4
%bcond_without  ui
%bcond_without  tools

Name:           preupgrade-assistant
Version:        2.2.0
Release:        1%{?dist}
Summary:        Preupgrade assistant
Group:          System Environment/Libraries
License:        GPLv3+
Source0:        %{name}-%{version}.tar.gz
Source1:        Django-%{django_version}.tar.gz
Source2:        south-%{south_version}.tar.gz

BuildRoot:      %{_tmppath}/%{pkg_name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
BuildRequires:  rpm-devel
BuildRequires:  python-devel
%if %{?_with_check:1}%{!?_with_check:0}
BuildRequires:  perl-XML-XPath
%endif
BuildRequires:  python-setuptools
BuildRequires:  rpm-python
BuildRequires:  diffstat
BuildRequires:  openscap%{?_isa} >= 0:1.2.8-1
BuildRequires:  openscap-engine-sce%{?_isa} >= 0:1.2.8-1
BuildRequires:  openscap-utils%{?_isa} >= 0:1.2.8-1
BuildRequires:  pykickstart
BuildRequires:  python-six
Requires(post):   /sbin/ldconfig
Requires(postun): /sbin/ldconfig
Requires:       coreutils grep gawk
Requires:       sed findutils bash
Requires:       openscap%{?_isa} >= 0:1.2.8-1
Requires:       openscap-engine-sce%{?_isa} >= 0:1.2.8-1
Requires:       openscap-utils%{?_isa} >= 0:1.2.8-1
Requires:       rpm-python
Requires:       redhat-release
Requires:       pykickstart
Requires:       yum-utils
Requires:       python-six
Conflicts:      %{name}-tools < 2.1.0-1
Obsoletes:      %{name} < 2.1.3-1

%description
Preupgrade assistant analyses the system to assess the feasibility of
upgrading the system to a new major version. Such analysis includes check for
removed packages, packages replaced by partially incompatible packages, changes
in libraries, users and groups and various services. Report of this analysis
can help admins with the system upgrade - by identification of potential
troubles and by mitigating some of the incompatibilities. Data gathered
by Preupgrade Assistant can be used for in-place upgrade or migration of the
system. Migrated system is a new system installation retaining as much of the
old system setup as possible.

%if 0%{?with_ui}
%package ui
Summary:    Preupgrade Assistant Web Based User Interface
Group:      System Environment/Libraries
Requires:   %{name}
Requires:   sqlite
Requires:   mod_wsgi
Requires:   %{name} = %{version}-%{release}

%description ui
Graphical interface for preupgrade assistant. This can be used
for inspecting results.
%endif # with_ui

%if 0%{?with_tools}
%package tools
Summary:    Preupgrade Assistant tools for generating contents
Group:      System Environment/Libraries
Provides:   preupg-xccdf-compose = %{version}-%{release}
Provides:   preupg-create-group-xml = %{version}-%{release}
Requires:   %{name} = %{version}-%{release}
Obsoletes:  %{name}-tools < 2.1.3-1
%description tools
Tools for generating contents used by preupgrade assistant. User
can specify only INI file and scripts and other stuff needed by
OpenSCAP is generated automatically.
%endif # with_tools

%prep
# Update timestamps on the files touched by a patch, to avoid non-equal
# .pyc/.pyo files across the multilib peers within a build, where "Level"
# is the patch prefix option (e.g. -p1)
UpdateTimestamps() {
    Level=$1
    PatchFile=$2
    # Locate the affected files:
    for f in $(diffstat $Level -l $PatchFile); do
        # Set the files to have the same timestamp as that of the patch:
        touch -r $PatchFile $f
    done
}

%setup -n %{name}-%{version} -q
%setup -n %{name}-%{version} -D -T -a 1
%setup -n %{name}-%{version} -D -T -a 2

%build
%{__python} setup.py build

%if 0%{?with_ui}
pushd Django-%{django_version}
%{__python} setup.py build
popd
pushd South-%{south_version}
%{__python} setup.py build
popd
%endif # with_ui

%check
# Swith off tests until issue with finding /etc/preupgrade-assistant.conf
# is resolved
#%%{__python} setup.py test

%install
install -d -m 755 $RPM_BUILD_ROOT%{_localstatedir}/log/preupgrade

%{__python} setup.py install --skip-build --root=$RPM_BUILD_ROOT

install -d -m 755 $RPM_BUILD_ROOT%{_mandir}/man1
install -p man/preupg.1 $RPM_BUILD_ROOT%{_mandir}/man1/
install -p man/preupgrade-assistant-api.1 $RPM_BUILD_ROOT%{_mandir}/man1/
install -p man/preupg-content-creator.1 $RPM_BUILD_ROOT%{_mandir}/man1/

####################
# WEB-UI packaging #
####################
%if 0%{?with_ui}

mkdir -m 644 -p ${RPM_BUILD_ROOT}%{_sharedstatedir}/preupgrade/{results,upload,static}
touch ${RPM_BUILD_ROOT}%{_sharedstatedir}/preupgrade/{db.sqlite,secret_key}

sed -r \
  -e "s;^DATA_DIR = .*$;DATA_DIR = '%{_sharedstatedir}/preupgrade';" \
  -i ${RPM_BUILD_ROOT}%{python_sitelib}/preupg/ui/settings.py

sed \
    -e 's;WSGI_PATH;%{python_sitelib}/preupg/ui/wsgi.py;g' \
    -e 's;STATIC_PATH;%{_sharedstatedir}/preupgrade/static;g' \
    -i ${RPM_BUILD_ROOT}%{_sysconfdir}/httpd/conf.d/99-preup-httpd.conf.{private,public}

##############################
# Django and South packaging #
##############################

# install django
pushd Django-%{django_version}
%{__python} setup.py install --skip-build --root ${RPM_BUILD_ROOT}
popd
pushd South-%{south_version}
%{__python} setup.py install --skip-build --root ${RPM_BUILD_ROOT}
popd

# remove .po files
find    ${RPM_BUILD_ROOT}%{python_sitelib}/django -name "*.po" | xargs rm -f

# remove bin/django-admin and *.egg-info
rm -rf  ${RPM_BUILD_ROOT}%{_bindir}/django-admin* \
        ${RPM_BUILD_ROOT}%{python_sitelib}/Django-%{django_version}-py*.egg-info \
        ${RPM_BUILD_ROOT}%{python_sitelib}/South-%{south_version}-py*.egg-info

# move django and south to preupg/ui/lib
mkdir   ${RPM_BUILD_ROOT}%{python_sitelib}/preupg/ui/lib
mv      ${RPM_BUILD_ROOT}%{python_sitelib}/{django,south} \
        ${RPM_BUILD_ROOT}%{python_sitelib}/preupg/ui/lib/

%else # with_ui

# If UI is not build up
rm -rf  ${RPM_BUILD_ROOT}%{python_sitelib}/preupg/ui/
rm -f   ${RPM_BUILD_ROOT}%{_bindir}/preupg-ui-manage

%endif # with_ui

###########################################################
## make special file lists for cleaner files section below
## - only for files under %%{python_sitelib}/preupg
########## preupgrade-assistant ###########################
# now just files
find ${RPM_BUILD_ROOT} -type f \
    | grep -o "%{python_sitelib}/.*$" \
    | grep -vE "preupg/(ui|creator)|\.pyc$" \
    | sed "s/\.py$/\.py\*/" > preupg-filelist

# now directories
find ${RPM_BUILD_ROOT} -type d \
    | grep -o "%{python_sitelib}/.*$" \
    | grep -vE "preupg/(ui|creator)" \
    | sed "s/^/\%dir /" >> preupg-filelist

########## preupgrade-assistant-ui ########################
# files
find ${RPM_BUILD_ROOT} -type f \
    | grep -o "%{python_sitelib}/preupg/ui.*$" \
    | grep -vE "/ui/settings.py|\.pyc$" \
    | sed "s/\.py$/\.py\*/" > preupg-ui-filelist

# directories
find ${RPM_BUILD_ROOT} -type d \
    | grep -o "%{python_sitelib}/preupg/ui.*$" \
    | sed "s/^/\%dir /" >> preupg-ui-filelist

##########################################################
# END FILELISTS
##########################################################

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/ldconfig

######### IF WITH-UI ##############################
%if 0%{?with_ui}

%post ui

# populate DB and/or apply DB migrations
su apache - -s /bin/bash -c "preupg-ui-manage syncdb --migrate --noinput" >/dev/null || :
# collect static files
su apache - -s /bin/bash -c "preupg-ui-manage collectstatic --noinput" >/dev/null || :
if [ "$1" == 1 ]; then
    # allow httpd to run preupgrade ui
    setsebool httpd_run_preupgrade on
fi
# restart apache
service httpd condrestart

%postun ui

# $1 holds the number of preupgrade-assistant-ui packages which will
# be left on the system when the uninstallation completes.
if [ "$1" == 0 ]; then
    # disallow httpd to run preupgrade ui
    setsebool httpd_run_preupgrade off
    # restart apache
    service httpd condrestart
fi

%endif # with_ui
######### ENDIF WITH-UI ###########################


%postun -p /sbin/ldconfig

%files -f preupg-filelist
%defattr(-,root,root,-)
%attr(0755,root,root) %{_bindir}/preupg
%attr(0755,root,root) %{_bindir}/premigrate
%attr(0755,root,root) %{_bindir}/preupg-kickstart-generator
%dir %{_localstatedir}/log/preupgrade
%dir %{_datadir}/preupgrade/
%dir %{_docdir}/%{name}
%config(noreplace) %{_sysconfdir}/preupgrade-assistant.conf
%{_sysconfdir}/bash_completion.d/preupg.bash
#%%{python_sitelib}/*.egg-info
%{_datadir}/preupgrade/data
%{_datadir}/preupgrade/common.sh
%doc %{_datadir}/preupgrade/README
%doc %{_datadir}/preupgrade/README.kickstart
%{!?_licensedir:%global license %%doc}
%license %{_docdir}/%{name}/LICENSE
%attr(0644,root,root) %{_mandir}/man1/preupg.*

%if 0%{?with_ui}
%files ui -f preupg-ui-filelist
%defattr(-,root,root,-)
%attr(0755,root,root) %{_bindir}/preupg-ui-manage
%verify(not md5 size mtime) %config %{python_sitelib}/preupg/ui/settings.py
%{python_sitelib}/preupg/ui/settings.py[c|o]
%config(noreplace) %{_sysconfdir}/httpd/conf.d/99-preup-httpd.conf.*
%attr(0744, apache, apache) %dir %{_sharedstatedir}/preupgrade/
%ghost %config(noreplace) %{_sharedstatedir}/preupgrade/db.sqlite
%ghost %config(noreplace) %{_sharedstatedir}/preupgrade/secret_key
%doc %{_datadir}/preupgrade/README.ui
%endif # with_ui

%if 0%{?with_tools}
%files tools
%defattr(-,root,root,-)
%attr(0755,root,root) %{_bindir}/preupg-create-group-xml
%attr(0755,root,root) %{_bindir}/preupg-xccdf-compose
%attr(0755,root,root) %{_bindir}/preupg-content-creator
%{python_sitelib}/preupg/creator/
%attr(0644,root,root) %{_mandir}/man1/preupgrade-assistant-api.*
%attr(0644,root,root) %{_mandir}/man1/preupg-content-creator.*
%endif # with_tools

%changelog

