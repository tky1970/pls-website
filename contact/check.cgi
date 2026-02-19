#!/usr/bin/perl

#┌─────────────────────────────────
#│ POST-MAIL : check.cgi - 2025/08/11
#│ copyright (c) kentweb, 1997-2025
#│ http://www.kent-web.com/
#└─────────────────────────────────

# モジュール宣言
use strict;
use CGI::Carp qw(fatalsToBrowser);

# 外部ファイル取り込み
require './init.cgi';
my %cf = set_init();

print <<EOM;
Content-type: text/html; charset=utf-8

<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Check Mode</title>
</head>
<body>
<b>Check Mode: [ $cf{version} ]</b>
<ul>
<li>Perlバージョン : $]
EOM

# ディレクトリ
for ( $cf{datadir}, "$cf{datadir}/ses" ) {
	if (-d $_) {
		print "<li>$_ ディレクトリパス : OK\n";
		
		if (-r $_ && -w $_ && -x $_) {
			print "<li>$_ ディレクトリパーミッション : OK\n";
		} else {
			print "<li>$_ ディレクトリパーミッション : NG\n";
		}
	} else {
		print "<li>$_ ディレクトリパス : NG\n";
	}
}

# ファイルチェック
for (qw(log.dat)) {
	if (-f "$cf{datadir}/$_") {
		print "<li>$cf{datadir}/$_ ファイルパス : OK\n";
		
		if (-r "$cf{datadir}/$_" && -w "$cf{datadir}/$_") {
			print "<li>$_ ファイルパーミッション : OK\n";
		} else {
			print "<li>$_ ファイルパーミッション : NG\n";
		}
	} else {
		print "<li>$_ ファイルパス : NG\n";
	}
}

# sendmailチェック
print "<li>sendmailパス : ";
if (-e $cf{sendmail}) {
	print "OK\n";
} else {
	print "NG\n";
}

# テンプレート
for (qw(conf.html error.html thanks.html mail.txt reply.txt)) {
	print "<li>テンプレート ( $_ ) : ";
	
	if (-f "$cf{tmpldir}/$_") {
		print "パスOK\n";
	} else {
		print "パスNG\n";
	}
}

my @bom = (
	chr(0x00).chr(0x00).chr(0xFE).chr(0xFF),
	chr(0xFF).chr(0xFE).chr(0x00).chr(0x00),
	chr(0x00).chr(0x00).chr(0xFF).chr(0xFE),
	chr(0xFE).chr(0xFF).chr(0x00).chr(0x00),
	chr(0xFE).chr(0xFF),
	chr(0xFF).chr(0xFE),
	chr(0xEF).chr(0xBB).chr(0xBF)
);

# BOMチェック
for (qw(mail.txt reply.txt)) {
	open(IN,"$cf{tmpldir}/$_");
	my $data = <IN>;
	close(IN);
	
	my $flg;
	for ( my $i = 0; $i <= $#bom; $i++ ) {
		if (index($data,$bom[$i]) == 0) {
			$flg++;
			last;
		}
	}
	if ($flg) {
		print "<li>本文 ( $_ ) BOMあり : NG\n";
	} else {
		print "<li>本文 ( $_ ) BOMなし : OK\n";
	}
}

print <<EOM;
</ul>
</body>
</html>
EOM
exit;

