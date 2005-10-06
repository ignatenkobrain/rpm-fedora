%define	with_python_subpackage	1%{nil}
%define	with_python_version	2.4%{nil}
%define	with_bzip2		1%{nil}
%define	with_apidocs		1%{nil}

# XXX legacy requires './' payload prefix to be omitted from rpm packages.
%define	_noPayloadPrefix	1

%define	__prefix	%{?_prefix}%{!?_prefix:/usr}
%{?!_lib: %define _lib lib}
%{expand: %%define __share %(if [ -d %{__prefix}/share/man ]; then echo /share ; else echo %%{nil} ; fi)}

%define __bindir	%{__prefix}/bin
%define __includedir	%{__prefix}/include
%define __libdir	%{__prefix}/%{_lib}
%define __mandir	%{__prefix}%{__share}/man

Summary: The RPM package management system.
Name: rpm
%define version 4.4.2
Version: %{version}
%{expand: %%define rpm_version %{version}}
Release: 5
Group: System Environment/Base
Source: ftp://wraptastic.org/pub/rpm-4.4.x/rpm-%{rpm_version}.tar.gz
Patch0: rpm-4.4.1-hkp-disable.patch
Patch1: rpm-4.4.1-fileconflicts.patch 
Patch2: rpm-4.4.1-prereq.patch
Patch3: rpm-4.4.1-nonmerged.patch
Patch4: rpm-4.4.1-prepostun.patch
Patch5: rpm-4.4.1-ordererase.patch
Patch6: rpm-4.4.2-matchpathcon.patch
Patch7: rpm-4.4.2-perlreq.patch
Patch8: rpm-4.4.2-db3-param.patch
Patch9: rpm-4.4.2-contextverify.patch
License: GPL
Conflicts: patch < 2.5
%ifos linux
Prereq: fileutils shadow-utils
%endif
Requires: popt = 1.10.2
Obsoletes: rpm-perl < %{version}

# XXX necessary only to drag in /usr/lib/libelf.a, otherwise internal elfutils.
BuildRequires: elfutils-libelf
BuildRequires: elfutils-devel

BuildRequires: sed readline-devel zlib-devel

BuildRequires: beecrypt-devel >= 4.1.2
Requires: beecrypt >= 4.1.2

BuildRequires: neon-devel
BuildRequires: sqlite-devel
BuildRequires: gettext-devel
BuildRequires: libselinux-devel

# XXX Red Hat 5.2 has not bzip2 or python
%if %{with_bzip2}
BuildRequires: bzip2-devel >= 0.9.0c-2
%endif
%if %{with_python_subpackage}
BuildRequires: python-devel >= %{with_python_version}
%endif

BuildRoot: %{_tmppath}/%{name}-root

%description
The RPM Package Manager (RPM) is a powerful command line driven
package management system capable of installing, uninstalling,
verifying, querying, and updating software packages. Each software
package consists of an archive of files along with information about
the package like its version, a description, etc.

%package libs
Summary:  Libraries for manipulating RPM packages.
Group: Development/Libraries

%description libs
This package contains the RPM shared libraries.

%package devel
Summary:  Development files for manipulating RPM packages.
Group: Development/Libraries
Requires: rpm = %{rpm_version}-%{release}
Requires: beecrypt >= 4.1.2
Requires: neon-devel
Requires: sqlite-devel
Requires: libselinux-devel
Requires: elfutils-libelf-devel

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
Summary: Scripts and executable programs used to build packages.
Group: Development/Tools
Requires: rpm = %{rpm_version}-%{release}, patch >= 2.5, file
Provides: rpmbuild(VendorConfig) = 4.1-1

%description build
The rpm-build package contains the scripts and executable programs
that are used to build packages using the RPM Package Manager.

%if %{with_python_subpackage}
%package python
Summary: Python bindings for apps which will manipulate RPM packages.
Group: Development/Libraries
Requires: rpm = %{rpm_version}-%{release}
Requires: python >= %{with_python_version}
Requires: elfutils >= 0.55

%description python
The rpm-python package contains a module that permits applications
written in the Python programming language to use the interface
supplied by RPM Package Manager libraries.

This package should be installed if you want to develop Python
programs that will manipulate RPM packages and databases.
%endif

%package -n popt
Summary: A C library for parsing command line parameters.
Group: Development/Libraries
Version: 1.10.2

%description -n popt
Popt is a C library for parsing command line parameters. Popt was
heavily influenced by the getopt() and getopt_long() functions, but it
improves on them by allowing more powerful argument expansion. Popt
can parse arbitrary argv[] style arrays and automatically set
variables based on command line arguments. Popt allows command line
arguments to be aliased via configuration files and includes utility
functions for parsing arbitrary strings into argv[] arrays using
shell-like rules.

%prep
%setup -q
%patch0 -p1  -b .nohkp
%patch1 -p1  -b .fileconflicts
%patch2 -p1  -b .prereq
%patch3 -p1  -b .rpmal
%patch4 -p1  -b .prepostun
%patch5 -p1  -b .ordererase
%patch6 -p1  -b .matchpathcon
%patch7 -p1  -b .perlreq
%patch8 -p1  -b .param
%patch9 -p1  -b .contextverify


%build

# XXX rpm needs functioning nptl for configure tests
unset LD_ASSUME_KERNEL || :

%if %{with_python_subpackage}
WITH_PYTHON="--with-python=%{with_python_version}"
%else
WITH_PYTHON="--without-python"
%endif

%ifos linux
CFLAGS="$RPM_OPT_FLAGS"; export CFLAGS
./configure --prefix=%{__prefix} --sysconfdir=/etc \
	--localstatedir=/var --infodir='${prefix}%{__share}/info' \
	--mandir='${prefix}%{__share}/man' \
	$WITH_PYTHON --enable-posixmutexes --without-javaglue
%else
export CPPFLAGS=-I%{__prefix}/include 
CFLAGS="$RPM_OPT_FLAGS" ./configure --prefix=%{__prefix} $WITH_PYTHON \
	--without-javaglue
%endif

make -C zlib || :

make %{?_smp_mflags}

%install
# XXX rpm needs functioning nptl for configure tests
unset LD_ASSUME_KERNEL || :

rm -rf $RPM_BUILD_ROOT

make DESTDIR="$RPM_BUILD_ROOT" install

# Working around breakage from the -L$(RPM_BUILD_ROOT)... -L$(DESTDIR)...
# workaround to #132435,
# and from linking to included zlib
for i in librpm.la librpmbuild.la librpmdb.la librpmio.la ; do
	sed -i -e 's~-L'"$RPM_BUILD_ROOT"'[^ ]* ~~g' \
		-e 's~-L'"$RPM_BUILD_DIR"'[^ ]* ~~g' \
		"$RPM_BUILD_ROOT%{__libdir}/$i"
done

# Clean up dangling symlinks
# XXX Fix in rpm tree
for i in /usr/bin/rpme /usr/bin/rpmi /usr/bin/rpmu; do
    rm -f "$RPM_BUILD_ROOT"/"$i" 
done

# Clean up dangling symlinks
for i in /usr/lib/rpmpopt /usr/lib/rpmrc; do
    rm -f "$RPM_BUILD_ROOT"/"$i" 
done

%ifos linux

# Save list of packages through cron
mkdir -p ${RPM_BUILD_ROOT}/etc/cron.daily
install -m 755 scripts/rpm.daily ${RPM_BUILD_ROOT}/etc/cron.daily/rpm

mkdir -p ${RPM_BUILD_ROOT}/etc/logrotate.d
install -m 644 scripts/rpm.log ${RPM_BUILD_ROOT}/etc/logrotate.d/rpm

mkdir -p $RPM_BUILD_ROOT/etc/rpm

mkdir -p $RPM_BUILD_ROOT/var/spool/repackage
mkdir -p $RPM_BUILD_ROOT/var/lib/rpm
for dbi in \
	Basenames Conflictname Dirnames Group Installtid Name Packages \
	Providename Provideversion Requirename Requireversion Triggername \
	Filemd5s Pubkeys Sha1header Sigmd5 \
	__db.001 __db.002 __db.003 __db.004 __db.005 __db.006 __db.007 \
	__db.008 __db.009
do
    touch $RPM_BUILD_ROOT/var/lib/rpm/$dbi
done

%endif

%if %{with_apidocs}
gzip -9n apidocs/man/man*/* || :
%endif

# Get rid of unpackaged files
{ cd $RPM_BUILD_ROOT
  rm -f .%{_libdir}/lib*.la
  rm -f .%{__prefix}/lib/rpm/{Specfile.pm,cpanflute,cpanflute2,rpmdiff,rpmdiff.cgi,sql.prov,sql.req,tcl.req}
  rm -rf .%{__mandir}/{fr,ko}
%if %{with_python_subpackage}
  rm -f .%{__libdir}/python%{with_python_version}/site-packages/*.{a,la}
  rm -f .%{__libdir}/python%{with_python_version}/site-packages/rpm/*.{a,la}
  rm -f .%{__libdir}/python%{with_python_version}/site-packages/rpmdb/*.{a,la}
%endif
}


%clean
rm -rf $RPM_BUILD_ROOT

%pre
%ifos linux
if [ -f /var/lib/rpm/packages.rpm ]; then
    echo "
You have (unsupported)
	/var/lib/rpm/packages.rpm	db1 format installed package headers
Please install rpm-4.0.4 first, and do
	rpm --rebuilddb
to convert your database from db1 to db3 format.
"
    exit 1
fi
/usr/sbin/groupadd -g 37 rpm				> /dev/null 2>&1
/usr/sbin/useradd  -r -d /var/lib/rpm -u 37 -g 37 rpm -s /sbin/nologin	> /dev/null 2>&1
%endif
exit 0

%post
%ifos linux
/sbin/ldconfig

# Establish correct rpmdb ownership.
/bin/chown rpm.rpm /var/lib/rpm/[A-Z]*

# XXX Detect (and remove) incompatible dbenv files during db-4.3.14 upgrade.
# XXX Removing dbenv files in %%post opens a lock race window, a tolerable
# XXX risk compared to the support issues involved with upgrading Berkeley DB.
[ -w /var/lib/rpm/__db.001 ] &&
/usr/lib/rpm/rpmdb_stat -CA -h /var/lib/rpm 2>&1 |
grep "db_stat: Program version 4.3 doesn't match environment version" 2>&1 > /dev/null &&
	rm -f /var/lib/rpm/__db*
                                                                                
%endif
exit 0

%ifos linux
%postun
/sbin/ldconfig
if [ $1 = 0 ]; then
    /usr/sbin/userdel rpm
    /usr/sbin/groupdel rpm
fi
exit 0

%post devel -p /sbin/ldconfig
%postun devel -p /sbin/ldconfig

%post -n popt -p /sbin/ldconfig
%postun -n popt -p /sbin/ldconfig
%endif

%if %{with_python_subpackage}
%post python -p /sbin/ldconfig
%postun python -p /sbin/ldconfig
%endif

%define	rpmattr		%attr(0755, rpm, rpm)

%files
%defattr(-,root,root)
%doc RPM-PGP-KEY RPM-GPG-KEY BETA-GPG-KEY CHANGES GROUPS doc/manual/[a-z]*
# XXX comment these lines out if building with rpm that knows not %pubkey attr
%pubkey RPM-PGP-KEY
%pubkey RPM-GPG-KEY
%pubkey BETA-GPG-KEY
%attr(0755, rpm, rpm)	/bin/rpm

%ifos linux
%config(noreplace,missingok)	/etc/cron.daily/rpm
%config(noreplace,missingok)	/etc/logrotate.d/rpm
%dir				/etc/rpm
#%config(noreplace,missingok)	/etc/rpm/macros.*
%attr(0755, rpm, rpm)	%dir /var/lib/rpm
%attr(0755, rpm, rpm)	%dir /var/spool/repackage

%define	rpmdbattr %attr(0644, rpm, rpm) %verify(not md5 size mtime) %ghost %config(missingok,noreplace)
%rpmdbattr	/var/lib/rpm/*
%endif

%rpmattr	%{__bindir}/rpm2cpio
%rpmattr	%{__bindir}/gendiff
%rpmattr	%{__bindir}/rpmdb
#%rpmattr	%{__bindir}/rpm[eiu]
%rpmattr	%{__bindir}/rpmsign
%rpmattr	%{__bindir}/rpmquery
%rpmattr	%{__bindir}/rpmverify

%attr(0755, rpm, rpm)	%dir %{__prefix}/lib/rpm
%rpmattr	%{__prefix}/lib/rpm/config.guess
%rpmattr	%{__prefix}/lib/rpm/config.sub
%rpmattr	%{__prefix}/lib/rpm/convertrpmrc.sh
%rpmattr	%{__prefix}/lib/rpm/freshen.sh
%attr(0644, rpm, rpm)	%{__prefix}/lib/rpm/macros
%rpmattr	%{__prefix}/lib/rpm/mkinstalldirs
%rpmattr	%{__prefix}/lib/rpm/rpm.*
%rpmattr	%{__prefix}/lib/rpm/rpm2cpio.sh
%rpmattr	%{__prefix}/lib/rpm/rpm[deiukqv]
%rpmattr	%{__prefix}/lib/rpm/tgpg
%attr(0644, rpm, rpm)	%{__prefix}/lib/rpm/rpmpopt*
%attr(0644, rpm, rpm)	%{__prefix}/lib/rpm/rpmrc

%ifarch i386 i486 i586 i686 athlon pentium3 pentium4
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/i[3456]86*
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/athlon*
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/pentium*
%endif
%ifarch alpha alphaev5 alphaev56 alphapca56 alphaev6 alphaev67
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/alpha*
%endif
%ifarch sparc sparcv8 sparcv9 sparc64
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/sparc*
%endif
%ifarch ia64
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/ia64*
%endif
%ifarch powerpc ppc ppciseries ppcpseries ppcmac ppc64
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/ppc*
%endif
%ifarch s390 s390x
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/s390*
%endif
%ifarch armv3l armv4l
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/armv[34][lb]*
%endif
%ifarch mips mipsel
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/mips*
%endif
%ifarch x86_64
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/x86_64*
%endif
%attr(-, rpm, rpm)		%{__prefix}/lib/rpm/noarch*

%rpmattr	%{__prefix}/lib/rpm/rpmdb_*
%rpmattr	%{__prefix}/lib/rpm/rpmfile

%lang(cs)	%{__prefix}/*/locale/cs/LC_MESSAGES/rpm.mo
%lang(da)	%{__prefix}/*/locale/da/LC_MESSAGES/rpm.mo
%lang(de)	%{__prefix}/*/locale/de/LC_MESSAGES/rpm.mo
%lang(fi)	%{__prefix}/*/locale/fi/LC_MESSAGES/rpm.mo
%lang(fr)	%{__prefix}/*/locale/fr/LC_MESSAGES/rpm.mo
%lang(gl)	%{__prefix}/*/locale/gl/LC_MESSAGES/rpm.mo
%lang(is)	%{__prefix}/*/locale/is/LC_MESSAGES/rpm.mo
%lang(ja)	%{__prefix}/*/locale/ja/LC_MESSAGES/rpm.mo
%lang(ko)	%{__prefix}/*/locale/ko/LC_MESSAGES/rpm.mo
%lang(no)	%{__prefix}/*/locale/no/LC_MESSAGES/rpm.mo
%lang(pl)	%{__prefix}/*/locale/pl/LC_MESSAGES/rpm.mo
%lang(pt)	%{__prefix}/*/locale/pt/LC_MESSAGES/rpm.mo
%lang(pt_BR)	%{__prefix}/*/locale/pt_BR/LC_MESSAGES/rpm.mo
%lang(ro)	%{__prefix}/*/locale/ro/LC_MESSAGES/rpm.mo
%lang(ru)	%{__prefix}/*/locale/ru/LC_MESSAGES/rpm.mo
%lang(sk)	%{__prefix}/*/locale/sk/LC_MESSAGES/rpm.mo
%lang(sl)	%{__prefix}/*/locale/sl/LC_MESSAGES/rpm.mo
%lang(sr)	%{__prefix}/*/locale/sr/LC_MESSAGES/rpm.mo
%lang(sv)	%{__prefix}/*/locale/sv/LC_MESSAGES/rpm.mo
%lang(tr)	%{__prefix}/*/locale/tr/LC_MESSAGES/rpm.mo

%{__mandir}/man1/gendiff.1*
%{__mandir}/man8/rpm.8*
%{__mandir}/man8/rpm2cpio.8*
%lang(ja)	%{__mandir}/ja/man[18]/*.[18]*
%lang(pl)	%{__mandir}/pl/man[18]/*.[18]*
%lang(ru)	%{__mandir}/ru/man[18]/*.[18]*
%lang(sk)	%{__mandir}/sk/man[18]/*.[18]*

%files libs
%defattr(-,root,root)
%{__libdir}/librpm-4.4.so
%{__libdir}/librpmdb-4.4.so
%{__libdir}/librpmio-4.4.so
%{__libdir}/librpmbuild-4.4.so

%files build
%defattr(-,root,root)
%dir %{__prefix}/src/redhat
%dir %{__prefix}/src/redhat/BUILD
%dir %{__prefix}/src/redhat/SPECS
%dir %{__prefix}/src/redhat/SOURCES
%dir %{__prefix}/src/redhat/SRPMS
%dir %{__prefix}/src/redhat/RPMS
%{__prefix}/src/redhat/RPMS/*
%rpmattr	%{__bindir}/rpmbuild
%rpmattr	%{__prefix}/lib/rpm/brp-*
%rpmattr	%{__prefix}/lib/rpm/check-files
%rpmattr	%{__prefix}/lib/rpm/check-prereqs
%rpmattr	%{__prefix}/lib/rpm/config.site
%rpmattr	%{__prefix}/lib/rpm/cross-build
%rpmattr	%{__prefix}/lib/rpm/debugedit
%rpmattr	%{__prefix}/lib/rpm/find-debuginfo.sh
%rpmattr	%{__prefix}/lib/rpm/find-lang.sh
%rpmattr	%{__prefix}/lib/rpm/find-prov.pl
%rpmattr	%{__prefix}/lib/rpm/find-provides
%rpmattr	%{__prefix}/lib/rpm/find-provides.perl
%rpmattr	%{__prefix}/lib/rpm/find-req.pl
%rpmattr	%{__prefix}/lib/rpm/find-requires
%rpmattr	%{__prefix}/lib/rpm/find-requires.perl
%rpmattr	%{__prefix}/lib/rpm/get_magic.pl
%rpmattr	%{__prefix}/lib/rpm/getpo.sh
%rpmattr	%{__prefix}/lib/rpm/http.req
%rpmattr	%{__prefix}/lib/rpm/javadeps
%rpmattr	%{__prefix}/lib/rpm/magic
%rpmattr	%{__prefix}/lib/rpm/magic.mgc
%rpmattr	%{__prefix}/lib/rpm/magic.mime
%rpmattr	%{__prefix}/lib/rpm/magic.mime.mgc
%rpmattr	%{__prefix}/lib/rpm/magic.prov
%rpmattr	%{__prefix}/lib/rpm/magic.req
%rpmattr	%{__prefix}/lib/rpm/perldeps.pl
%rpmattr	%{__prefix}/lib/rpm/perl.prov
%rpmattr	%{__prefix}/lib/rpm/perl.req
%rpmattr	%{__prefix}/lib/rpm/pythondeps.sh

%rpmattr	%{__prefix}/lib/rpm/rpm[bt]
%rpmattr	%{__prefix}/lib/rpm/rpmdeps
%rpmattr	%{__prefix}/lib/rpm/trpm
%rpmattr	%{__prefix}/lib/rpm/u_pkg.sh
%rpmattr	%{__prefix}/lib/rpm/vpkg-provides.sh
%rpmattr	%{__prefix}/lib/rpm/vpkg-provides2.sh

%{__mandir}/man8/rpmbuild.8*
%{__mandir}/man8/rpmdeps.8*

%if %{with_python_subpackage}
%files python
%defattr(-,root,root)
%{__libdir}/python%{with_python_version}/site-packages/rpm
%endif

%files devel
%defattr(-,root,root)
%if %{with_apidocs}
%doc apidocs
%endif
%{__includedir}/rpm
%{__libdir}/librpm.a
%{__libdir}/librpm.la
%{__libdir}/librpm.so
%{__libdir}/librpmdb.a
%{__libdir}/librpmdb.la
%{__libdir}/librpmdb.so
%{__libdir}/librpmio.a
%{__libdir}/librpmio.la
%{__libdir}/librpmio.so
%{__libdir}/librpmbuild.a
%{__libdir}/librpmbuild.la
%{__libdir}/librpmbuild.so
%{__mandir}/man8/rpmcache.8*
%{__mandir}/man8/rpmgraph.8*
%rpmattr	%{__prefix}/lib/rpm/rpmcache
%rpmattr	%{__bindir}/rpmgraph

%files -n popt
%defattr(-,root,root)
%{__libdir}/libpopt.so.*
%{__mandir}/man3/popt.3*
%lang(cs)	%{__prefix}/*/locale/cs/LC_MESSAGES/popt.mo
%lang(da)	%{__prefix}/*/locale/da/LC_MESSAGES/popt.mo
%lang(de)	%{__prefix}/*/locale/de/LC_MESSAGES/popt.mo
%lang(es)	%{__prefix}/*/locale/es/LC_MESSAGES/popt.mo
%lang(eu_ES)	%{__prefix}/*/locale/eu_ES/LC_MESSAGES/popt.mo
%lang(fi)	%{__prefix}/*/locale/fi/LC_MESSAGES/popt.mo
%lang(fr)	%{__prefix}/*/locale/fr/LC_MESSAGES/popt.mo
%lang(gl)	%{__prefix}/*/locale/gl/LC_MESSAGES/popt.mo
%lang(hu)	%{__prefix}/*/locale/hu/LC_MESSAGES/popt.mo
%lang(id)	%{__prefix}/*/locale/id/LC_MESSAGES/popt.mo
%lang(is)	%{__prefix}/*/locale/is/LC_MESSAGES/popt.mo
%lang(it)	%{__prefix}/*/locale/it/LC_MESSAGES/popt.mo
%lang(ja)	%{__prefix}/*/locale/ja/LC_MESSAGES/popt.mo
%lang(ko)	%{__prefix}/*/locale/ko/LC_MESSAGES/popt.mo
%lang(no)	%{__prefix}/*/locale/no/LC_MESSAGES/popt.mo
%lang(pl)	%{__prefix}/*/locale/pl/LC_MESSAGES/popt.mo
%lang(pt)	%{__prefix}/*/locale/pt/LC_MESSAGES/popt.mo
%lang(pt_BR)	%{__prefix}/*/locale/pt_BR/LC_MESSAGES/popt.mo
%lang(ro)	%{__prefix}/*/locale/ro/LC_MESSAGES/popt.mo
%lang(ru)	%{__prefix}/*/locale/ru/LC_MESSAGES/popt.mo
%lang(sk)	%{__prefix}/*/locale/sk/LC_MESSAGES/popt.mo
%lang(sl)	%{__prefix}/*/locale/sl/LC_MESSAGES/popt.mo
%lang(sr)	%{__prefix}/*/locale/sr/LC_MESSAGES/popt.mo
%lang(sv)	%{__prefix}/*/locale/sv/LC_MESSAGES/popt.mo
%lang(tr)	%{__prefix}/*/locale/tr/LC_MESSAGES/popt.mo
%lang(uk)	%{__prefix}/*/locale/uk/LC_MESSAGES/popt.mo
%lang(wa)	%{__prefix}/*/locale/wa/LC_MESSAGES/popt.mo
%lang(zh)	%{__prefix}/*/locale/zh/LC_MESSAGES/popt.mo
%lang(zh_CN)	%{__prefix}/*/locale/zh_CN/LC_MESSAGES/popt.mo
%lang(zh_TW)	%{__prefix}/*/locale/zh_TW/LC_MESSAGES/popt.mo

# XXX These may end up in popt-devel but it hardly seems worth the effort.
%{__libdir}/libpopt.a
%{__libdir}/libpopt.la
%{__libdir}/libpopt.so
%{__includedir}/popt.h

%changelog
* Thu Sep 22 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.2-5
- Actually fix context verification where matchpathcon fails (#162037)

* Fri Aug 26 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.2-4
- Fix build with CFLAGS having --param
- Fix for context verification in /tmp (#162037)

* Wed Jul 27 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.2-3
- popt minor version requires

* Tue Jul 26 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.2-2
- popt minor version bump
- revert to perl.req/perl.prov for now

* Thu Jul 21 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.2-1
- Upgrade to upstream release

* Tue May 24 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.1-21
- Update translations (#154623)

* Sat May 21 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.1-20
- Drop signature patch
- dangling unpackaged symlinks

* Tue May 17 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.1-19
- Check for symlinks in check-files (#108778)
- Move zh_CN (#154623)
- Test fix for signing old rpms (#127113)

* Wed May 04 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.1-18.1
- Fix typo
- Fix typo

* Wed May 04 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.1-18
- Add missing fsm.c from matchpathcon patches 

* Tue May 03 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.1-17
- Fix typo

* Tue May 03 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.1-16
- Yet more matchpathcon

* Tue May 03 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.1-15
- Some more matchpathcon work

* Mon May 02 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.1-14
- matchpathcon fixup

* Mon May 02 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.1-13
- Use matchpathcon (#151870)

* Sat Apr 30 2005 Miloslav Trmac <mitr@redhat.com> - 4.4.1-12
- Remove $RPM_BUILD_ROOT and $RPM_BUILD_DIR from distribued .la files (#116891)
- Don't ship static version of _rpmdb.so
- BuildRequires: readline-devel

* Wed Apr 27 2005 Paul Nasrat <pnasrat@redhat.com> - 4.4.1-11
- Fix for (pre,postun) (#155700)
- Erase ordering

* Wed Apr 27 2005 Jeremy Katz <katzj@redhat.com> - 4.4.1-10
- add patch to fix segfault with non-merged hdlists

* Thu Mar 31 2005 Thomas Woerner <twoerner@redhat.com> 4.4.1-9
- enabled prereqs again

* Mon Mar 21 2005 Paul Nasrat <pnasrat@redhat.com> 4.4.1-8
- Add devel requires libselinux-devel
- Fileconflicts as FC3 (#151609)

* Wed Mar  9 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-7
- rebuild against renamed sqlite package (#149719).

* Mon Mar  7 2005 Jeremy Katz <katzj@redhat.com> - 4.4.1-6
- fix build with new glibc

* Mon Mar  7 2005 Jeremy Katz <katzj@redhat.com> - 4.4.1-5
- disable hkp by default

* Tue Mar  1 2005 Jeremy Katz <katzj@redhat.com> - 4.4.1-4
- fix build with gcc 4

* Mon Feb 28 2005 Jeremy Katz <katzj@redhat.com> - 4.4.1-3
- fix posttrans callback check being backwards (#149524)

* Sun Feb 13 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-1
- don't classify files in /dev (#146623).
- don't build with sqlite3 if <sqlite3.h> is missing.

* Sat Feb 12 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-0.24
- zlib: uniqify certain symbols to prevent name space pollution.
- macosx: include <sys/types.h> so that python sees the u_char typedef.
- macosx: change to --prefix=/usr rather than /opt/local.
- use waitpid rather than SIGCHLD reaper.
- rip out DB_PRIVATE revert if not NPTL, it's not the right thing to do.

* Fri Feb 11 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-0.22
- permit build scriptlet interpreters to be individually overridden.

* Thu Feb 10 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-0.20
- perform callbacks as always (#147537).

* Wed Feb  2 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-0.16
- fix: length of gpg V4 hash seed was incorrect (#146896).
- add support for V4 rfc-2440 signatures.

* Mon Jan 31 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-0.14
- add sqlite internal (build still expects external sqlite3-3.0.8).
- sqlite: revert to original narrow scoping of cOpen/cClose.

* Fri Jan 28 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-0.12
- python: force dbMatch() h# key to be 32 bit integer (#146477).

* Tue Jan 25 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-0.10
- more macosx fiddles.
- move global /var/lock/rpm/transaction to dbpath.
- permit fcntl path to be configured through rpmlock_path macro.
- add missing #if defined(ENABLE_NLS) (#146184).

* Mon Jan 17 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-0.8
- changes to build on Mac OS X using darwinports neon/beecrypt.
- add https://svn.uhulinux.hu/packages/dev/zlib/patches/02-rsync.patch

* Sun Jan  9 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-0.7
- build against external/internal neon.

* Tue Jan  4 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-0.6
- mac os x patches (#131943,#131944,#132924,#132926).
- mac os x patches (#133611, #133612, #134637).

* Sun Jan  2 2005 Jeff Johnson <jbj@jbj.org> 4.4.1-0.5
- upgrade to db-4.3.27.
- revert MAGIC_COMPRESS, real fix is in libmagic (#143782).
- upgrade to file-4.12 internal.

* Tue Dec  7 2004 Jeff Johnson <jbj@jbj.org> 4.4.1-0.3
- use package color as Obsoletes: color.

* Mon Dec  6 2004 Jeff Johnson <jbj@jbj.org> 4.4.1-0.2
- automagically detect and emit "python(abi) = 2.4" dependencies.
- popt 1.10.1 to preserve newer.

* Sun Dec  5 2004 Jeff Johnson <jbj@jbj.org> 4.4.1-0.1
- force *.py->*.pyo byte code compilation with brp-python-bytecompile.
