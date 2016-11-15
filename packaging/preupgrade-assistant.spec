%{!?scl:%global pkg_name %{name}}

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

%global         django_version  1.5.5
%global         south_version   0.8.4
%bcond_without  ui
%bcond_without  tools

Name:           preupgrade-assistant
Version:        2.1.10
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

## make special file lists for cleaner files section below
find ${RPM_BUILD_ROOT} -type f | grep -o "%{python_sitelib}/preupg/ui/.*$" \
    | grep -v "/ui/settings.py" | grep -v "\.pyc$" \
    | sed "s/\.py$/\.py\*/" > preupg-ui-filelist
find ${RPM_BUILD_ROOT} -type f | grep -o "%{python_sitelib}/preupg/.*$" \
    | grep -v "preupg/ui" | grep -v "\.pyc$" \
    | sed "s/\.py$/\.py\*/" > preupg-filelist

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
%define egg_name %(echo %{name} | sed s/-/_/)
%{python_sitelib}/%{egg_name}*.egg-info
%config(noreplace) %{_sysconfdir}/preupgrade-assistant.conf
%{_sysconfdir}/bash_completion.d/preupg.bash
%{_datadir}/preupgrade/
%exclude %{_datadir}/preupgrade/README*
%doc %{_datadir}/preupgrade/README
%doc %{_datadir}/preupgrade/README.kickstart
%{!?_licensedir:%global license %%doc}
%license /usr/share/doc/preupgrade-assistant/LICENSE
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
* Mon Oct 10 2016 Petr Hracek <phracek@redhat.com> - 2.1.10-6
- default value in script type is not picked on Enter
- Related: #1332792

* Wed Oct 05 2016 Petr Hracek <phracek@redhat.com> - 2.1.10-5
- Fix binary_req is ignored
- Resolves: #1380139

* Tue Oct 04 2016 Petr Hracek <phracek@redhat.com> - 2.1.10-4
- Fix deploy_hook to proper directory
- Resolves: #1381359

* Tue Sep 27 2016 Petr Hracek <phracek@redhat.com> - 2.1.10-3
- Fix several deploy_hook bugs
- Resolves: #1378191, #1378205, #1378215, #1378219

* Wed Sep 21 2016 Petr Hracek <phracek@redhat.com> - 2.1.10-2
- Fix regression in debug messages
- Resolves: #1371701

* Wed Sep 21 2016 Petr Hracek <phracek@redhat.com> - 2.1.10-1
- Support full path in deploy_hook function
- Related #1334903

* Mon Sep 19 2016 Petr Hracek <phracek@redhat.com> - 2.1.9-9
- Fix dist-mode is ignored
- get_dist_native_list is broken
- Resolves: #1376640
- Resolves: #1375813

* Thu Sep 15 2016 Petr Hracek <phracek@redhat.com> - 2.1.9-8
- Fix deploy_hook function. Returns exit_error statuses
- Related #1334903

* Wed Sep 14 2016 Petr Hracek <phracek@redhat.com> - 2.1.9-7
- Fix MODULE_PATH is empty or not defined
- Resolves #1334903

* Wed Sep 14 2016 Petr Hracek <phracek@redhat.com> - 2.1.9-6
- Fix documentation
- Resolves: #1272917

* Wed Sep 07 2016 Petr Hracek <phracek@redhat.com> - 2.1.9-5
- Revert return values to previous state.
- Resolves: #1373493

* Mon Sep 05 2016 Petr Hracek <phracek@redhat.com> - 2.1.9-4
- Remove print in check_inplace_risk function
- Resolves: #1372870

* Thu Sep 01 2016 Petr Hracek <phracek@redhat.com> - 2.1.9-3
- preupg return code: Fix fail without risk is error
- Resolves: #1362659

* Wed Aug 31 2016 Petr Hracek <phracek@redhat.com> - 2.1.9-2
- Update dependencies to the newest openscap-1.2.8
- Resolves #1371832

* Thu Aug 25 2016 Petr Hracek <phracek@redhat.com> - 2.1.9-1
- Fix return values
- Resolves #1362659

* Wed Aug 24 2016 Petr Hracek <phracek@redhat.com> - 2.1.8-7
- Fix deploy_hook function
- Related #1334903

* Mon Aug 22 2016 Petr Hracek <phracek@redhat.com> - 2.1.8-6
- Fix order of exist values

* Mon Aug 22 2016 Petr Hracek <phracek@redhat.com> - 2.1.8-5
- Missing files in tarball
- Resolves #1352171
- Related #1361715

* Wed Aug 17 2016 Petr Hracek <phracek@redhat.com> - 2.1.8-4
- Fix NONE risk. Another patch
- Related #1331629

* Tue Aug 16 2016 Petr Hracek <phracek@redhat.com> - 2.1.8-3
- Fix return values
- Removing all sys.exit calling
- Resolves #1361715

* Fri Jul 29 2016 Petr Hracek <phracek@redhat.com> - 2.1.8-2
- Fixes build modules and prints output in case of wrong assessment
- Resolves #1361489

* Tue Jul 26 2016 Petr Hracek <phracek@redhat.com> - 2.1.8-1
- Several documentation updates (#1272917)
- Updated tests for kickstart generation

* Wed Jul 13 2016 Petr Hracek <phracek@redhat.com> - 2.1.7.post21-1
- Fix issues caused by prompt

* Fri Jul 01 2016 Petr Hracek <phracek@redhat.com> - 2.1.7.post18-1
- This version fixes several bugs
- Resolves #1309536, #1330883, #1334903
- Resolves #1332777, #1332792, #1325393
- Resolves #1331629

* Tue Jun 07 2016 Petr Hracek <phracek@redhat.com> - 2.1.6.post41-6
- Move preupgrade.ks file to kickstart directory
  Resolves: #1318602

* Fri Apr 29 2016 Petr Stodulka <pstodulk@redhat.com> - 2.1.6-5
- fix parsing of configuration file
  Resolves: #1256685

* Thu Apr 28 2016 Petr Hracek <phracek@redhat.com> - 2.1.6-4
- Modify kickstart generation based on preupgrade-assistant-el6toel7 data

* Tue Apr 26 2016 Petr Hracek <phracek@redhat.com> - 2.1.6-3
- Fix traceback preupg-content-creator
- Fix problem with generating assessment for specific mode
  Resolves: #1317124
  Resolves: #1330716

* Fri Apr 22 2016 Petr Stodulka <pstodulk@redhat.com> - 2.1.6-2
- remove old sources and patch
- resolves xsl pain - patch was removed previously, so added back
  modified patch, suitable to current version of PA: 2.1.6
  Resolves: #1304772 #1312702


* Wed Apr 20 2016 Petr Hracek <phracek@redhat.com> - 2.1.6-1
- Fix package kickstart generation
  Resolves: #1261291

* Mon Apr 11 2016 Petr Stodulka <pstodulk@redhat.com> - 2.1.5-5
- fix API for python's scripts - check of installed packages
  Resolves: #1318431

* Wed Mar 16 2016 Petr Stodulka <pstodulk@redhat.com> - 2.1.5-4
- fix wrong condition in check_applies_to which evaluates if
  script is applicable or not; negation of the condition
  Resolves: #1318431

* Tue Mar 08 2016 Petr Hracek <phracek@redhat.com> - 2.1.5-3
- Fix for preupg-content-creator. Introduce manual pages
  Resolves: #1253682

* Wed Mar 02 2016 Petr Stodulka <pstodulk@redhat.com> - 2.1.5-2
- solve xsl pain for now, modified preup.xsl
  - correction of paths and remove section which implies dump info
    in html with new OpenSCAP
  - added xsl files from openscap 1.0.8-1 to our xsl directory
  - reverted part of previous fix
  Resolves: #1304772 #1312702

* Fri Feb 26 2016 Petr Hracek <phracek@redhat.com> - 2.1.5-1
- New upstream release with several bugs
- Kickstart bugs
- API are the same
- UI fixes
  Resolves: #1310056, #1293410, #1302267, #1302278, #1302303,
  Resolves: #1302309, #1310056

* Thu Feb 18 2016 Petr Stodulka <pstodulk@redhat.com> - 2.1.4-10
- fix syntax error in previous patch
  Resolves: #1309519

* Mon Feb 15 2016 Petr Stodulka <pstodulk@redhat.com> - 2.1.4-9
- fix common.sh - use local variable instead of global

* Mon Feb 15 2016 Petr Stodulka <pstodulk@redhat.com> - 2.1.4-8
- Fix function get_dist_native_list in common.sh
  Resolves: #1256685

* Mon Feb 08 2016 Petr Hracek <phracek@redhat.com> - 2.1.4-7
- Fix for report generation is broken
- Resolves: #1304772

* Fri Jan 22 2016 Petr Hracek <phracek@redhat.com> - 2.1.4-6
- Staticdata are part of content path

* Fri Jan 08 2016 Petr Hracek <phracek@redhat.com> - 2.1.4-5
- Devel mode has own section in configuration file

* Thu Jan 07 2016 Jakub DorÅˆÃ¡k <jdornak@redhat.com> - 2.1.4-4
- Fixed expanding and collapsing of results in UI
  Resolves: #1231400

* Thu Jan 07 2016 Petr Stodulka <pstodulk@redhat.com> - 2.1.4-3
- fix changes due to preupgrade-assistant-staticdata (keep common directory
  with its content)
- add function get_dist_native_list to API
- modify is_dist_native
    - return True/False in python
    - use log_warning instead of log_info when package is removed
  Resolves: #1256685, #1296298

* Wed Jan 06 2016 Jakub DorÅˆÃ¡k <jdornak@redhat.com> - 2.1.4-2
- Add README.ui
  Resolves: #1225844

* Wed Jan 06 2016 Petr Hracek <phracek@redhat.com> - 2.1.4-1
- New upstream release 2.1.4

* Tue Dec 22 2015 Petr Hracek <phracek@redhat.com> - 2.1.3-3
- Fix typo in preupgrade-assistant-devel.patch

* Wed Dec 09 2015 Petr Hracek <phracek@redhat.com> - 2.1.3-2
- Add patch for DEVEL_MODE

* Wed Dec 09 2015 Petr Hracek <phracek@redhat.com> - 2.1.3-1
- New upstream release 2.1.3

* Tue Oct 27 2015 Petr Hracek <phracek@redhat.com> - 2.1.1-5
- Rebuild for fast errata refresh.

* Mon Oct 26 2015 Petr Hracek <phracek@redhat.com> - 2.1.1-4
- Another rebuild because of QA testing.

* Mon Oct 26 2015 Petr Hracek <phracek@redhat.com> - 2.1.1-3
- Rebuild because of QA testing.

* Mon Sep 14 2015 Petr Hracek <phracek@redhat.com> - 2.1.1-2
- Update changelog
- New upstream release 2.1.1
- kickstart fixes

* Wed Sep 09 2015 Petr Hracek <phracek@redhat.com> - 2.1.0-7
- Include /tmp/part-include into kickstart file
  Resolves (#1252916)

* Tue Sep 08 2015 Petr Hracek <phracek@redhat.com> - 2.1.0-6
- Use RHRHEL7rpmlist file instead of RHRHEL7rpmlist_kept

* Tue Sep 08 2015 Petr Hracek <phracek@redhat.com> - 2.1.0-5
- fix common.sh script

* Tue Sep 08 2015 Petr Hracek <phracek@redhat.com> - 2.1.0-4
- Add patch for common.sh

* Mon Sep 07 2015 Petr Hracek <phracek@redhat.com> - 2.1.0-3
- Info what to do with pre-generated kickstart
  Resolves (#1253680)

* Mon Sep 07 2015 Petr Hracek <phracek@redhat.com> - 2.1.0-2
- API with path to static lists
- symbolic link to complete set of variants
- preupg --kickstart informs to run preupg
  Resolves (#1247921, #1254586, #1260008)

* Thu Aug 13 2015 Petr Hracek <phracek@redhat.com> - 2.1.0-1
- New upstream version 2.1.0
  Resolves #1215685
  Resolves #1229790

* Wed Jul 29 2015 Petr Hracek <phracek@redhat.com> - 2.0.3-12
- RFE Provide a configuration file override implementation
  for customized symbolic links
  Resolves #1234557

* Thu Jun 18 2015 Petr Hracek <phracek@redhat.com> - 2.0.3-11
- Fix for placeholder text instead of Solution
  Resolves #1232961

* Wed Jun 17 2015 Petr Stodulka <pstodulk@redhat.com> - 2.0.3-10
- recover patch from 2.0.3-7 - original rhbz #1225758
  Resolves #1232863

* Wed Jun 17 2015 Petr Hracek <phracek@redhat.com> - 2.0.3-9
- Placeholder text instead of Solution
  Resolves #1229810
- Incomplete items in result-admin.html
  Resolves #1229877

* Thu May 28 2015 Jakub DorÅˆÃ¡k <jdornak@redhat.com> - 2.0.3-8
- Apply UI changes
  Resolves #1196166

* Thu May 28 2015 Jakub DorÅˆÃ¡k <jdornak@redhat.com> - 2.0.3-7
- fix call of get_file_content
  Resolves #1225758

* Wed May 20 2015 Petr Stodulk <pstodulk@redhat.com> - 2.0.3-3
- Correction of *six patch - stdout must be init by 'str()' as binary type
  otherwise we can get ascii error due to previous performance fix
  Resolves #1222935

* Wed May 20 2015 Petr Hracek <phracek@redhat.com> - 2.0.3-2
- Test if python-six exists in python sources
  Resolves #1222935

* Tue May 19 2015 Petr Hracek <phracek@redhat.com> -2.0.3-1
- Fix for admin and user reports
  Related: #1212810

* Wed May 13 2015 Petr Stodulka <pstodulk@redhat.com> - 2.0.2-1
- PA was rebased in some previous commit, so bump version
- Fix performance problems
  Resolves: #1221138

* Thu May 07 2015 Petr Hracek <phracek@redhat.com> - 2.0.1-16
- Add pykickstart to Requires
- Fix RepoData.patch

* Wed Apr 29 2015 Petr Hracek <phracek@redhat.com> - 2.0.1-15
Resolves: #1215965

* Mon Apr 13 2015 Petr Hracek <phracek@redhat.com> - 2.0.1-14
- Add missing patch for RepoData

* Fri Apr 10 2015 Petr Hracek <phracek@redhat.com> - 2.0.1-13
- Resolves #1209782 Preupgrade freezes and never ends in i686 arch

* Tue Mar 17 2015 Petr Hracek <phracek@redhat.com> - 2.0.1-12
- Mode option doesn't process any contents (#1203141)
- Add support migrate and upgrade to check scripts (#1200033)

* Tue Mar 17 2015 Petr Hracek <phracek@redhat.com> - 2.0.1-11
- Add support migrate and upgrade to check scripts (#1200033)

* Tue Mar 17 2015 Petr Stodulka <pstodulk@redhat.com> - 2.0.1-10
- Added requires: redhat-release
  Solve issue with missing /etc/redhat-release, which is for us
  best solution for detection of system variant.

* Mon Mar 16 2015 Petr Hracek <phracek@redhat.com> - 2.0.1-9
- Fix problem with decoding

* Wed Mar 11 2015 Petr Hracek <phracek@redhat.com> - 2.0.1-8
- Wrong dependencies in preupgrade-assistant

* Tue Mar 10 2015 Petr Hracek <phracek@redhat.com> - 2.0.1-7
- Multilib problems add missing BuildRequires

* Tue Mar 10 2015 Petr Hracek <phracek@redhat.com> - 2.0.1-6
- Multilib problems

* Mon Mar 09 2015 Petr Hracek <phracek@redhat.com> - 2.0.1-5
- Unable to open file kickstart/untrackeduser (#1188280)
- preupg --upload requires slash after submit (#1195250)

* Fri Dec 12 2014 Jakub DorÅˆÃ¡k <jdornak@redhat.com> - 2.0.1-4
- Update selinux related stuff
Resolves: #1150019

* Fri Nov 21 2014 Petr Hracek <phracek@redhat.com> - 2.0.1-3
- Wrong terminal output
- correct man page and help message
Resolves #1157443

* Thu Sep 04 2014 Petr Hracek <phracek@redhat.com> - 2.0.1-1
- Fix for correct return value in case of usage --riskcheck
Resolves: #1148878

* Thu Sep 04 2014 Petr Hracek <phracek@redhat.com> - 2.0.0-2
- preupgrade lists user home directory content in /var/cache/preupgrade
- provide descriptive error message (#1125228)
- Usability: suggest to install UI (#1125286)
Resolves: #1106498

* Tue Aug 05 2014 Petr Hracek <phracek@redhat.com> - 2.0.0-1
- Remove building openscap (#1113887)

* Wed Jul 30 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-37
- Preupgrade-assistant should be able to do cleanup of his files (#1123774)

* Tue Jul 29 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-36
- Don't verify db.sqlite and ui.log files

* Fri Jul 18 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-35
- Add support check_description
Resolves: #1078334

* Tue Jul 01 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-34
- Fix in case of calling preupg -c <contents>
- New package preupgrade-assistant-tools
- Removing some obsolete files
- Rename utils to preuputils dir
Resolves: #1113890

* Fri Jun 06 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-33
- rpm -V issue in preupgrade-assistant-ui package
Resolves: #1105482

* Thu Jun 05 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-32
Resolves: #1105120
- preupgrade-assistant doesn't check file updates

* Wed Jun 04 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-31
- Related: #1100192 Some fixes in HTML output

* Wed Jun 04 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-30
- Related: #1100192 Proper update of solution texts

* Thu May 29 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-29
- Add LICENSE text (#1102778)
- use rcue instead of patternfly rhbz#1102789

* Tue May 27 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-28
- Do not ship setuid binary (#1101698)
- Use correct preupg extension in config files

* Thu May 22 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-27
- Resolves: #1100192 Copy modified configuration files

* Wed May 21 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-26
- Fix for inplacerisk links

* Fri May 16 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-25
- Fix for running contents

* Thu May 15 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-24
- Support for repo metadata

* Wed May 14 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-23
- Fix for command log files traceback

* Mon May 12 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-22
- Fixes in solution text files
- Show only selected number of rules

* Mon May 05 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-21
- Support a 3rdpart contents

* Tue Apr 29 2014 Pavel Raiskup <praiskup@redhat.com> - 1.0.2-20
- fix for unowned directories

* Fri Apr 25 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-19
- Fix: prefix issue #(1091074)

* Thu Apr 10 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-18
- Fixes in order to support premigrate command

* Mon Apr 07 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-17
- Fix API usage from redhat-upgrade-tool (#1084983)

* Thu Mar 27 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-16
- other fixes in setup.py

* Tue Mar 25 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-15
- Huge Python refactoring
- fix in setup.py

* Tue Mar 25 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-14
- Several Python fixes
- XML enhancement
- Supporting premigrate contents in /usr/share/premigrate

* Fri Mar 21 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-13
- Several fixes found during QA test days

* Wed Mar 19 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-12
- Text improvements
- debug option used for oscap output
- premigrate script for migration scenario

* Wed Mar 19 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-11
- Man page introduced
- Needs inspection in HTML page
- More enhancements in UI
- Improved CLI
- Several fixes

* Thu Mar 13 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-10
- Fix the bug #1075853

* Wed Mar 12 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-9
- new upstream version
- remove DEBUG info in case of no --debug option
- Introduced new states needs_action and needs_inspection
- several fixes

* Fri Mar 07 2014 Tomas Tomecek <ttomecek@redhat.com> - 1.0.2-8
- package UI: new package -ui
- cleanup

* Tue Feb 11 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-6
- Fix in common.sh
- Add user interactive messages

* Mon Feb 10 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-5
- Fix the problem with logger
- If all-xccdf.xml is not found in /usr/share/preupgrade then print message
- Remove all yaml directives

* Mon Feb 03 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-4
- New option riskcheck for preupgrade-assistant analysis
- Option will be mainly used by redhat-upgrade-tool

* Tue Jan 28 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-3
- Introduced special tags for solution texts

* Tue Jan 21 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-2
- adding postupgrade.d scripts
- logs are updated only in case of RPM database change

* Mon Jan 13 2014 Petr Hracek <phracek@redhat.com> - 1.0.2-1
- Update to the latest openscap version

* Fri Jan 10 2014 Petr Hracek <phracek@redhat.com> - 1.0.1-14
- Introduce remediation
- Some python fixes and improvements

* Tue Dec 17 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-13
- Using INI files instead of YAML
- Introduce tests in spec file
- Fix using preupg -c option

* Wed Dec 11 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-12
- Support more txt files in content directory
- Do not ship web-ui yet
- Bump preupgrade-assistant version

* Tue Dec 10 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-11
- Bump wrapper version because of API changes
- Functions have comments
- Reference to KICKSTART_README file
- /root/preupgrade/common directory is deleted
- dirtyconf and cleanconf directories are introduced

* Tue Dec 10 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-10
- Update description text

* Mon Dec 09 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-9
- Add README file
- more tests for OSCAP functionality

* Mon Dec 09 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-8
- Add progress bar during gathering common logs
- Copy some common files to kickstart

* Mon Dec 09 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-7
- python refactoring
- HTML escape fixes
- Add correct usage of <br/> tag

* Thu Dec 05 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-6
- post_script.txt file for post scan issues
- Introduce --scan option for scanning
- Introduce --list-contents for getting list of contents
- Introduce --check option for testing contents by maintainers

* Thu Dec 05 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-5
- Correct parsing rpm_qa.log in API

* Wed Dec 04 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-4
- solution text and solution script can be together a content

* Wed Dec 04 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-3
- description field does not used any HTML tag

* Wed Dec 04 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-2
- Introduce more tests
- Functions for postupgrade case
- Use <br> tag instead of <p> in HTML description

* Mon Dec 02 2013 Petr Hracek <phracek@redhat.com> - 1.0.1-1
- Bump to new upstream openscap release

* Mon Dec 02 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-18
- group_title is not needed anymore in YAML files
- Correct requirements in spec file
- with statement has not to be used in python code
- Add RHEL5 building issue
- correct XML generation in case of missing YAML values

* Thu Nov 28 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-17
- preupgrade-assistant-contents-users is not part of the spec file
- Hide some debug logs
- group_title is not needed anymore in YAML files
- All solution text will be replace automatically at the end

* Thu Nov 28 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-16
- All python sources are part of preupgrade-assistant package

* Wed Nov 27 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-15
- Solution text can be HTML
- Add license texts
- Execute preupgrade assistant without argument
- More contents

* Mon Nov 25 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.9.11-14
- remove argparse dependency (use builtin optparse)

* Mon Nov 25 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-13
- Correct HTML syntax in solution text files

* Mon Nov 25 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-12
- SOLUTION_MSG has prefix which regards to content

* Sat Nov 23 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-11
- directory /var/cache/preupgrade/common is create automatically

* Fri Nov 22 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-10
- YAML is needed for the build

* Fri Nov 22 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-9
- New return value from content exit_failed (reference to exit_fail)

* Thu Nov 21 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-8
- YAML is not needed anymore
- New contents types
- Fixing BASH API

* Wed Nov 20 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-7
- Fix for current directory tag with relative path to all-xccdf.xml

* Tue Nov 19 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-6
- solution_file is introduced
- content dir is part of XML value.
- more generated functions like check_applies_to and check_rpm_to
- YAML is not needed for building RPMs anymore

* Wed Nov 06 2013 Pavel Raiskup <praiskup@redhat.com> 0.9.11-5
- rebuild to package recent upstream work

* Mon Nov 04 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-4
- common API is moved to preupgrade-assistant package

* Mon Nov 04 2013 Petr Hracek <phracek@redhat.com> - 0.9.11-4
- Fixed problems with wrong content

* Fri Nov 01 2013 Petr Hracek <phracek@redhat.com> 0.9.11-3
- Python refactoring and content definition

* Thu Oct 10 2013 Petr Hracek <phracek@redhat.com> 0.9.11-2
- temporary directory will be /var/tmp/preupgrade
- some corrections in create_group_xml.py and xccdf_compose.py files

* Thu Sep 12 2013 Petr Hracek <phracek@redhat.com> 0.9.11-1
- New openscap upstream version
- Supporting common modules

* Mon Dec 17 2012 Petr Hracek <phracek@redhat.com> 0.9.3-1
- Initial rpm

