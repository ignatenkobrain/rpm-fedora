# rawhide doesn't have new enough lzma yet
%bcond_with lzma
# sqlite backend is broken atm, disabled for now
%bcond_with sqlite
# just for giggles, option to build with internal Berkeley DB
%bcond_with int_bdb

%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

%define rpmhome /usr/lib/rpm

%define rpmver 4.5.90
%define snapver git8461
%define srcver %{rpmver}.%{snapver}

%define bdbver 4.5.20

Summary: The RPM package management system
Name: rpm
Version: %{rpmver}
Release: 0.%{snapver}.2
Group: System Environment/Base
Url: http://www.rpm.org/
Source0: http://rpm.org/releases/testing/%{name}-%{srcver}.tar.bz2
%if %{with int_bdb}
Source1: db-%{bdbver}.tar.gz
%endif

Patch0: rpm-4.5.90-devel-autodep.patch
Patch1: rpm-4.5.90-pkgconfig-path.patch
# XXX only create provides for pkgconfig and libtool initially
Patch100: rpm-4.6.x-no-pkgconfig-reqs.patch

# Already in upstream, remove on next snapshot update
Patch200: rpm-4.5.90-archivesize.patch

# These are not yet upstream
Patch300: rpm-4.5.90-posttrans.patch

# Partially GPL/LGPL dual-licensed and some bits with BSD
# SourceLicense: (GPLv2+ and LGPLv2+ with exceptions) and BSD 
License: GPLv2+

Requires(post): coreutils
Requires: popt >= 1.10.2.1
Requires: crontabs
Requires: logrotate
Requires: curl

%if %{without int_bdb}
# XXX using BDB 4.5.20 from compat-db for now to provide a safe downgrade
# route to older rpm. Only compat-db >= 4.6.21 has the necessary symlinks
# for building however.
BuildRequires: compat-db >= 4.6.21-2.fc10
%endif

# XXX generally assumed to be installed but make it explicit as rpm
# is a bit special...
BuildRequires: redhat-rpm-config
BuildRequires: gawk
BuildRequires: elfutils-devel >= 0.112
BuildRequires: elfutils-libelf-devel
BuildRequires: readline-devel zlib-devel
BuildRequires: nss-devel
# The popt version here just documents an older known-good version
BuildRequires: popt-devel >= 1.10.2
BuildRequires: file-devel
BuildRequires: gettext-devel
BuildRequires: libselinux-devel
BuildRequires: ncurses-devel
BuildRequires: bzip2-devel >= 0.9.0c-2
BuildRequires: python-devel >= 2.2
BuildRequires: lua-devel >= 5.1
%if %{with lzma}
BuildRequires: lzma-devel >= 4.42
%endif
%if %{with sqlite}
BuildRequires: sqlite-devel
%endif

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
The RPM Package Manager (RPM) is a powerful command line driven
package management system capable of installing, uninstalling,
verifying, querying, and updating software packages. Each software
package consists of an archive of files along with information about
the package like its version, a description, etc.

%package libs
Summary:  Libraries for manipulating RPM packages
Group: Development/Libraries
License: GPLv2+ and LGPLv2+ with exceptions
Requires: rpm = %{version}-%{release}

%description libs
This package contains the RPM shared libraries.

%package devel
Summary:  Development files for manipulating RPM packages
Group: Development/Libraries
License: GPLv2+ and LGPLv2+ with exceptions
Requires: rpm = %{version}-%{release}
Requires: pkgconfig
Requires: nss-devel 
Requires: libselinux-devel
Requires: elfutils-libelf-devel
Requires: popt-devel
%if %{with lzma}
Requires: lzma-devel >= 4.42
%endif
%if %{with sqlite}
Requires: sqlite-devel
%endif

%description devel
This package contains the RPM C library and header files. These
development files will simplify the process of writing programs that
manipulate RPM packages and databases. These files are intended to
simplify the process of creating graphical package managers or any
other tools that need an intimate knowledge of RPM packages in order
to function.

This package should be installed if you want to develop programs that
will manipulate RPM packages and databases.

%package build
Summary: Scripts and executable programs used to build packages
Group: Development/Tools
Requires: rpm = %{version}-%{release}
Requires: elfutils >= 0.128 binutils
Requires: findutils sed grep gawk diffutils file patch >= 2.5
Requires: unzip gzip bzip2 cpio lzma

%description build
The rpm-build package contains the scripts and executable programs
that are used to build packages using the RPM Package Manager.

%package python
Summary: Python bindings for apps which will manipulate RPM packages
Group: Development/Libraries
Requires: rpm = %{version}-%{release}

%description python
The rpm-python package contains a module that permits applications
written in the Python programming language to use the interface
supplied by RPM Package Manager libraries.

This package should be installed if you want to develop Python
programs that will manipulate RPM packages and databases.

%package apidocs
Summary: API documentation for RPM libraries
Group: Documentation

%description apidocs
This package contains API documentation for developing applications
that will manipulate RPM packages and databases.

%prep
%setup -q -n %{name}-%{srcver} %{?with_int_bdb:-a 1}
%patch0 -p1 -b .devel-autodep
%patch1 -p1 -b .pkgconfig-path
%patch100 -p1 -b .pkgconfig-deps

%patch200 -p1 -b .archivesize

# needs a bit of upstream love first...
#%patch300 -p1 -b .posttrans

%if %{with int_bdb}
ln -s db-%{bdbver} db
%endif

%build
%if %{without int_bdb}
export CPPFLAGS=-I%{_includedir}/db%{bdbver} 
export LDFLAGS=-L%{_libdir}/db%{bdbver}
%endif

%configure \
    %{!?with_int_bdb: --with-external-db} \
    %{?with_sqlite: --enable-sqlite3} \
    --with-lua \
    --with-selinux \
    --enable-python

make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT

make DESTDIR="$RPM_BUILD_ROOT" install

# Save list of packages through cron
mkdir -p ${RPM_BUILD_ROOT}%{_sysconfdir}/cron.daily
install -m 755 scripts/rpm.daily ${RPM_BUILD_ROOT}%{_sysconfdir}/cron.daily/rpm

mkdir -p ${RPM_BUILD_ROOT}%{_sysconfdir}/logrotate.d
install -m 644 scripts/rpm.log ${RPM_BUILD_ROOT}%{_sysconfdir}/logrotate.d/rpm

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/rpm

mkdir -p $RPM_BUILD_ROOT/var/lib/rpm
for dbi in \
    Basenames Conflictname Dirnames Group Installtid Name Packages \
    Providename Provideversion Requirename Requireversion Triggername \
    Filedigests Pubkeys Sha1header Sigmd5 \
    __db.001 __db.002 __db.003 __db.004 __db.005 __db.006 __db.007 \
    __db.008 __db.009
do
    touch $RPM_BUILD_ROOT/var/lib/rpm/$dbi
done

%find_lang %{name}

find $RPM_BUILD_ROOT -name "*.la"|xargs rm -f

%clean
rm -rf $RPM_BUILD_ROOT

%post libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig

%posttrans
# XXX this is klunky and ugly, rpm itself should handle this
%if %{with int_bdb}
dbstat=/usr/lib/rpm/rpmdb_stat
%else
dbstat=%{_bindir}/db45_stat
%endif
if [ -x "$dbstat" ]; then
    if "$dbstat" -e -h /var/lib/rpm 2>&1 | grep -q "Invalid argument"; then
        rm -f /var/lib/rpm/__db.* 
    fi
fi
exit 0

%files -f %{name}.lang
%defattr(-,root,root,-)
%doc CHANGES GROUPS COPYING CREDITS ChangeLog doc/manual/[a-z]*

%{_sysconfdir}/cron.daily/rpm
%config(noreplace,missingok)    %{_sysconfdir}/logrotate.d/rpm
%dir                            %{_sysconfdir}/rpm

%attr(0755, root, root)   %dir /var/lib/rpm
%attr(0644, rpm, rpm) %verify(not md5 size mtime) %ghost %config(missingok,noreplace) /var/lib/rpm/*
%attr(0755, root, root) %dir %{rpmhome}

/bin/rpm
%{_bindir}/rpm2cpio
%{_bindir}/rpmdb
%{_bindir}/rpmsign
%{_bindir}/rpmquery
%{_bindir}/rpmverify

%{_mandir}/man8/rpm.8*
%{_mandir}/man8/rpm2cpio.8*

# XXX this places translated manuals to wrong package wrt eg rpmbuild
%lang(fr) %{_mandir}/fr/man[18]/*.[18]*
%lang(ko) %{_mandir}/ko/man[18]/*.[18]*
%lang(ja) %{_mandir}/ja/man[18]/*.[18]*
%lang(pl) %{_mandir}/pl/man[18]/*.[18]*
%lang(ru) %{_mandir}/ru/man[18]/*.[18]*
%lang(sk) %{_mandir}/sk/man[18]/*.[18]*

%{rpmhome}/macros
%{rpmhome}/rpmpopt*
%{rpmhome}/rpmrc

%{rpmhome}/rpmdb_*
%{rpmhome}/rpm.daily
%{rpmhome}/rpm.log
%{rpmhome}/rpm.xinetd
%{rpmhome}/rpm2cpio.sh
%{rpmhome}/tgpg

%{rpmhome}/platform

%files libs
%defattr(-,root,root)
%{_libdir}/librpm*-*.so

%files build
%defattr(-,root,root)
%{_bindir}/rpmbuild
%{_bindir}/gendiff

%{_mandir}/man1/gendiff.1*

%{rpmhome}/brp-*
%{rpmhome}/check-buildroot
%{rpmhome}/check-files
%{rpmhome}/check-prereqs
%{rpmhome}/check-rpaths*
%{rpmhome}/debugedit
%{rpmhome}/find-debuginfo.sh
%{rpmhome}/find-lang.sh
%{rpmhome}/find-provides
%{rpmhome}/find-requires
%{rpmhome}/javadeps
%{rpmhome}/mono-find-provides
%{rpmhome}/mono-find-requires
%{rpmhome}/osgideps.pl
%{rpmhome}/perldeps.pl
%{rpmhome}/libtooldeps.sh
%{rpmhome}/pkgconfigdeps.sh
%{rpmhome}/perl.prov
%{rpmhome}/perl.req
%{rpmhome}/tcl.req
%{rpmhome}/pythondeps.sh
%{rpmhome}/rpmdeps
%{rpmhome}/config.guess
%{rpmhome}/config.sub
%{rpmhome}/mkinstalldirs
%{rpmhome}/rpmdiff*

%{rpmhome}/macros.perl
%{rpmhome}/macros.python
%{rpmhome}/macros.php

%{_mandir}/man8/rpmbuild.8*
%{_mandir}/man8/rpmdeps.8*

%files python
%defattr(-,root,root)
%{python_sitearch}/rpm

%files devel
%defattr(-,root,root)
%{_includedir}/rpm
%{_libdir}/librp*[a-z].so
%{_mandir}/man8/rpmgraph.8*
%{_bindir}/rpmgraph

%{_libdir}/pkgconfig/rpm.pc

%files apidocs
%defattr(-,root,root)
%doc doc/librpm/html/*

%changelog
* Wed Aug 13 2008 Panu Matilainen <pmatilai@redhat.com>
- 4.5.90-0.git8461.2
- fix archivesize tag generation on ppc (#458817)

* Fri Aug 08 2008 Panu Matilainen <pmatilai@redhat.com>
- 4.5.90-0.git8461.1
- new snapshot from upstream
- fixes #68290, #455972, #446202, #453364, #456708, #456103, #456321, #456913,
  #458260, #458261
- partial fix for #457360

* Thu Jul 31 2008 Florian Festi <ffesti@redhat.com>
- 4.5.90-0.git8427.1
- new snapshot from upstream

* Thu Jul 31 2008 Florian Festi <ffesti@redhat.com>
- 4.5.90-0.git8426.10
- rpm-4.5.90-posttrans.patch
- use header from rpmdb in posttrans to make anaconda happy

* Sat Jul 19 2008 Panu Matilainen <pmatilai@redhat.com>
- 4.5.90-0.git8426.9
- fix regression in patch number handling (#455872)

* Tue Jul 15 2008 Panu Matilainen <pmatilai@redhat.com>
- 4.5.90-0.git8426.8
- fix regression in macro argument handling (#455333)

* Mon Jul 14 2008 Panu Matilainen <pmatilai@redhat.com>
- 4.5.90-0.git8426.7
- fix mono dependency extraction (adjust for libmagic string change)

* Sat Jul 12 2008 Panu Matilainen <pmatilai@redhat.com>
- 4.5.90-0.git8426.6
- fix type mismatch causing funky breakage on ppc64

* Fri Jul 11 2008 Panu Matilainen <pmatilai@redhat.com>
- 4.5.90-0.git8426.5
- flip back to external bdb
- fix tab vs spaces complaints from rpmlint
- add dep for lzma and require unzip instead of zip in build (#310694)
- add pkgconfig dependency to rpm-devel
- drop ISA-dependencies for initial introduction
- new snapshot from upstream for documentation fixes

* Thu Jul 10 2008 Panu Matilainen <pmatilai@redhat.com>
- 4.5.90-0.git8424.4
- handle int vs external db in posttrans too

* Wed Jul 08 2008 Panu Matilainen <pmatilai@redhat.com>
- 4.5.90-0.git8424.3
- require curl as external url helper

* Wed Jul 08 2008 Panu Matilainen <pmatilai@redhat.com>
- 4.5.90-0.git8424.2
- add support for building with or without internal db

* Wed Jul 08 2008 Panu Matilainen <pmatilai@redhat.com>
- rpm 4.5.90-0.git8424.1 (alpha snapshot)
- adjust to build against Berkeley DB 4.5.20 from compat-db for now
- add posttrans to clean up db environment mismatch after upgrade
- forward-port devel autodeps patch

* Tue Jul 08 2008 Panu Matilainen <pmatilai@redhat.com>
- adjust for rpmdb index name change
- drop unnecessary vendor-macro patch for real
- add ISA-dependencies among rpm subpackages
- make lzma and sqlite deps conditional and disabled by default for now

* Fri Feb 01 2008 Panu Matilainen <pmatilai@redhat.com>
- spec largely rewritten, truncating changelog
