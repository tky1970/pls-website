#!/usr/bin/perl

#┌─────────────────────────────────
#│ POST-MAIL : postmail.cgi - 2025/08/11
#│ copyright (c) kentweb, 1997-2025
#│ http://www.kent-web.com/
#└─────────────────────────────────

# モジュール実行
use strict;
use CGI::Carp qw(fatalsToBrowser);
use lib './lib';
use CGI::Minimal;
use CGI::Session;

require './lib/jacode.pl';
require './init.cgi';
my %cf = set_init();

# データ受理
CGI::Minimal::max_read_size($cf{maxdata});
my $cgi = CGI::Minimal->new;
error('容量オーバー') if ($cgi->truncated);
my ($key,$need,$in) = parse_form();

# 禁止ワードチェック
if ($cf{no_wd}) { check_word(); }

# ホスト取得＆チェック
my ($host,$addr) = get_host();

# 必須入力チェック
my ($check,@err);
if ($$in{need} or @$need > 0) {
	# needフィールドの値を必須配列に加える
	my @tmp = split(/\s+/,$$in{need});
	push(@$need,@tmp);
	
	# 必須配列の重複要素を排除
	my %count;
	@$need = grep {!$count{$_}++} @$need;
	
	# 必須項目の入力値をチェックする
	for (@$need) {
		
		# フィールドの値が投げられてこないもの（ラジオボタン等）
		if (!defined $$in{$_}) {
			$check++;
			push(@$key,$_);
			push(@err,$_);
		
		# 入力なしの場合
		} elsif ($$in{$_} eq "") {
			$check++;
			push(@err,$_);
		}
	}
}

# 入力内容マッチ
my ($match1,$match2);
if ($$in{match}) {
	($match1,$match2) = split(/\s+/,$$in{match},2);
	
	if ($$in{$match1} ne $$in{$match2}) {
		error("$match1と$match2の再入力内容が異なります");
	}
}

# 入力チェック確認画面
if ($check) { err_input($match2); }

# --- プレビュー
if ($$in{mode} ne "send") {
	# 連続送信チェック
	check_post('view');
	
	# 確認画面
	prev_form();

# --- 送信実行
} else {
	# sendmail送信
	send_mail();
}

#-----------------------------------------------------------
#  プレビュー
#-----------------------------------------------------------
sub prev_form {
	# 送信内容チェック
	error("データを取得できません") if (@$key == 0);
	
	# メール書式チェック
	check_email($$in{email}) if ($$in{email});
	
	# 時間取得
	my $time = time;
	
	# 順番
	if ($$in{sort}) {
		my (@tmp,%tmp);
		for ( split(/\s+/,$$in{sort}) ) {
			push(@tmp,$_);
			$tmp{$_}++;
		}
		for (@$key) {
			if (!defined $tmp{$_}) { push(@tmp,$_); }
		}
		@$key = @tmp;
	}
	
	# 連結
	my %join;
	if ($$in{join}) {
		my ($key,$val) = split(/:/,$$in{join},2);
		my $tmp;
		for ( split(/\s+/,$val) ) {
			$tmp .= $$in{$_} . $_ ;
			$join{$_}++;
		}
		$$in{$key} = $tmp;
	}
	
	# セッション生成
	my $ses = new CGI::Session(undef,undef,{Directory => "$cf{datadir}/ses"}) or die CGI::Session->errstr();
	$ses->expire('+30m'); # 有効期限
	my $sesid = $ses->id(); # セッションID
	
	# テンプレート読込
	open(IN,"$cf{tmpldir}/conf.html") or error("open err: conf.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	# 置き換え
	$tmpl =~ s/!mail_cgi!/$cf{mail_cgi}/g;
	
	# テンプレート分割
	my ($head,$loop,$foot) = $tmpl =~ m|(.+)<!-- cell -->(.+)<!-- /cell -->(.+)|s
			? ($1,$2,$3)
			: error("テンプレート不正");
	
	# 引数
	my $hidden;
	$hidden .= qq|<input type="hidden" name="mode" value="send">\n|;
	$hidden .= qq|<input type="hidden" name="sesid" value="$sesid">\n|;
	if ($cf{recaptcha} == 1) {
		$hidden .= qq|<input type="hidden" id="g-recaptcha-response" name="g-recaptcha-response">|;
	}
	
	$ses->param("mode","send");
	
	# 項目
	my ($bef,$item,$jflg,$keys);
	for my $key (@$key) {
		next if ($bef eq $key);
		next if ($key eq "x");
		next if ($key eq "y");
		next if ($key eq "need");
		next if ($key eq "match");
		next if ($key eq "sort");
		next if ($key eq "join");
		next if ($$in{match} && $key eq $match2);
		next if ($jflg && defined $join{$key});
		if ($$in{join} && defined $join{$key}) {
			$jflg++;
			($key) = (split(/:/,$$in{join}))[0];
		}
		$keys .= "$key<>";
		
		$$in{$key} =~ s/(\t+)$//g;
		$ses->param($key,$$in{$key});
		
		# 改行変換
		$$in{$key} =~ s/\t/<br>/g;
		
		my $tmp = $loop;
		if (defined $cf{replace}{$key}) {
			$tmp =~ s/!key!/$cf{replace}{$key}/;
		} else {
			$tmp =~ s/!key!/$key/;
		}
		$tmp =~ s/!val!/$$in{$key}/;
		$item .= $tmp;
		
		$bef = $key;
	}
	$keys =~ s/(<>)$//;
	$ses->param("_KEYS",$keys);
	
	for ($head,$foot) {
		if ($cf{recaptcha} == 1) {
			s/<!-- gr_api -->/$cf{gr_api}/;
			s/<!-- gr_key -->/$cf{gr_key}/;
		}
		s/<!-- hidden -->/$hidden/g;
	}
	
	# セッション掃除
	ses_clean();
	
	# 画面展開
	print "Content-type: text/html; charset=utf-8\n\n";
	print $head,$item;
	
	# フッタ表示
	footer($foot);
}

#-----------------------------------------------------------
#  送信実行
#-----------------------------------------------------------
sub send_mail {
	my $gscore;
	if ($cf{recaptcha} == 1) {
		require "./lib/recaptcha.pl";
		my $ret = recaptcha($cf{secret_key},$$in{'g-recaptcha-response'});
		if (!$ret or $ret < $cf{recap_score}) {
			error("不正なリクエストです。");
		}
		$gscore = $ret;
	}
	
	# 送信内容チェック
	error("データを取得できません") if (@$key == 0);
	
	# 連続送信チェック
	check_post('send');
	
	# 時間取得
	my ($date1,$date2) = get_time();
	
	# ブラウザ情報
	my $agent = $ENV{HTTP_USER_AGENT};
	$agent =~ s/[<>&"'()+;]//g;
	
	$$in{sesid} =~ s/\W//g;
	my $ses = CGI::Session->load(undef,$$in{sesid},{Directory => "$cf{datadir}/ses"}) or die CGI::Session->errstr();
	if ($ses->is_empty) { error("二重送信又はセッションIDが無効です"); }
	my $keys = $ses->param('_KEYS');
	
	# 本文テンプレ読み込み
	open(IN,"$cf{tmpldir}/mail.txt") or error("open err: mail.txt");
	my $mail = join('',<IN>);
	close(IN);
	
	# テンプレ変数変換
	$mail =~ s/!date!/$date1/g;
	$mail =~ s/!agent!/$agent/g;
	$mail =~ s/!host!/$host/g;
	$mail .= "Google recaptchaスコア : $gscore\n";
	
	# 自動返信ありのとき
	my $reply;
	if ($cf{auto_res}) {
		# テンプレ
		open(IN,"$cf{tmpldir}/reply.txt") or error("open err: reply.txt");
		$reply = join('',<IN>);
		close(IN);
		
		# 変数変換
		$reply =~ s/!date!/$date1/g;
	}
	
	# 本文キーを展開
	my ($mbody,$log);
	for ( split(/<>/,$keys) ) {
		my $val = $ses->param($_);
		
		# エスケープ
		$val =~ s/\.\n/\. \n/g;
		
		# 添付ファイル風の文字列拒否
		$val =~ s/Content-Disposition:\s*attachment;.*//ig;
		$val =~ s/Content-Transfer-Encoding:.*//ig;
		$val =~ s/Content-Type:\s*multipart\/mixed;\s*boundary=.*//ig;
		
		# 改行復元
		$val =~ s/\t/\n/g;
		
		# HTMLタグ復元
		$val =~ s/&lt;/</g;
		$val =~ s/&gt;/>/g;
		$val =~ s/&quot;/"/g;
		$val =~ s/&#39;/'/g;
		$val =~ s/&amp;/&/g;
		
		if ($val =~ /\n/) { $val = "\n" . $val; }
		my $key = defined $cf{replace}{$_} ? $cf{replace}{$_} : $_;
		$mbody .= "$key = $val\n";
	}
	
	# 本文テンプレ内の変数を置き換え
	$mail =~ s/!message!/$mbody/;
	
	# 返信テンプレ内の変数を置き換え
	$reply =~ s/!message!/$mbody/ if ($cf{auto_res});
	
	# コード変換
	if ($cf{send_b64} == 1) {
		require './lib/base64.pl';
		$mail  = conv_b64($mail);
		$reply = conv_b64($reply) if ($cf{auto_res});
	
	} else {
		my $tmp;
		for my $ml ( split(/\n/,$mail) ) {
			jcode::convert(\$ml,'jis','utf8');
			$tmp .= "$ml\n";
		}
		$mail = $tmp;
		
		if ($cf{auto_res}) {
			my $tmp;
			for my $ml ( split(/\n/,$reply) ) {
				jcode::convert(\$ml,'jis','utf8');
				$tmp .= "$ml\n";
			}
			$reply = $tmp;
		}
	}
	$ses->delete();
	
	# メールアドレスがない場合は送信先に置換
	my $email = $ses->param('email') or $cf{mailto};
	
	# MIMEエンコード
	my $name    = $ses->param('name');
	my $sub_me = mime_unstructured_header($cf{subject});
	my $from;
	if ($name) {
		$name =~ s/[\r\n]//g;
		$from = mime_unstructured_header("\"$name\" <$email>");
	} else {
		$from = $email;
	}
	
	# --- 送信内容フォーマット開始
	# ヘッダー
	my $body;
	$body .= "To: $cf{mailto}\n";
	$body .= "From: $from\n";
	$body .= "Subject: $sub_me\n";
	$body .= "MIME-Version: 1.0\n";
	$body .= "Date: $date2\n";
	
	if ($cf{send_b64} == 1) {
		$body .= "Content-type: text/plain; charset=utf-8\n";
		$body .= "Content-Transfer-Encoding: base64\n";
	} else {
		$body .= "Content-type: text/plain; charset=iso-2022-jp\n";
		$body .= "Content-Transfer-Encoding: 7bit\n";
	}
	
	$body .= "X-Mailer: $cf{version}\n\n";
	$body .= "$mail\n";
	
	# 返信内容フォーマット
	my $res_body;
	if ($cf{auto_res}) {
		
		# 件名MIMEエンコード
		my $re_sub = mime_unstructured_header($cf{sub_reply});
		
		$res_body .= "To: $email\n";
		$res_body .= "From: $cf{mailto}\n";
		$res_body .= "Subject: $re_sub\n";
		$res_body .= "MIME-Version: 1.0\n";
		$res_body .= "Date: $date2\n";
		
		if ($cf{send_b64} == 1) {
			$res_body .= "Content-type: text/plain; charset=utf-8\n";
			$res_body .= "Content-Transfer-Encoding: base64\n";
		} else {
			$res_body .= "Content-type: text/plain; charset=iso-2022-jp\n";
			$res_body .= "Content-Transfer-Encoding: 7bit\n";
		}
		
		$res_body .= "X-Mailer: $cf{version}\n\n";
		$res_body .= "$reply\n";
	}
	
	# senmdailコマンド
	my $scmd = $cf{send_fcmd} ? "$cf{sendmail} -t -i -f $email" : "$cf{sendmail} -t -i";
	
	# 本文送信
	open(MAIL,"| $scmd") or error("メール送信失敗");
	print MAIL "$body\n";
	close(MAIL);
	
	# 返信送信
	if ($cf{auto_res}) {
		my $scmd = $cf{send_fcmd} ? "$cf{sendmail} -t -i -f $cf{mailto}" : "$cf{sendmail} -t -i";
		
		open(MAIL,"| $scmd") or error("メール送信失敗");
		print MAIL "$res_body\n";
		close(MAIL);
	}
	
	# リロード
	if ($cf{reload}) {
		if ($ENV{PERLXS} eq "PerlIS") {
			print "HTTP/1.0 302 Temporary Redirection\r\n";
			print "Content-type: text/html\n";
		}
		print "Location: $cf{back}\n\n";
		exit;
	
	# 完了メッセージ
	} else {
		open(IN,"$cf{tmpldir}/thanks.html") or error("open err: thanks.html");
		my $tmpl = join('',<IN>);
		close(IN);
		
		# 表示
		print "Content-type: text/html; charset=utf-8\n\n";
		$tmpl =~ s/!back!/$cf{back}/g;
		footer($tmpl);
	}
}

#-----------------------------------------------------------
#  入力エラー表示
#-----------------------------------------------------------
sub err_input {
	my $match2 = shift;
	
	# 順番
	if ($$in{sort}) {
		my (@tmp,%tmp);
		for ( split(/\s+/,$$in{sort}) ) {
			push(@tmp,$_);
			$tmp{$_}++;
		}
		for (@$key) {
			if (!defined $tmp{$_}) { push(@tmp,$_); }
		}
		@$key = @tmp;
	}
	
	# テンプレート読み込み
	open(IN,"$cf{tmpldir}/error.html") or die;
	my $tmpl = join('',<IN>);
	close(IN);
	
	# テンプレート分割
	my ($head,$loop,$foot) = $tmpl =~ m|(.+)<!-- cell -->(.+)<!-- /cell -->(.+)|s
			? ($1,$2,$3)
			: error("テンプレート不正");
	
	# ヘッダ
	print "Content-type: text/html; charset=utf-8\n\n";
	print $head;
	
	# 内容展開
	my $bef;
	for my $key (@$key) {
		next if ($key eq "need");
		next if ($key eq "match");
		next if ($key eq "sort");
		next if ($$in{match} && $key eq $match2);
		next if ($bef eq $key);
		next if ($key eq "x");
		next if ($key eq "y");
		
		my $key_name = defined $cf{replace}{$key} ? $cf{replace}{$key} : $key;
		my $tmp = $loop;
		$tmp =~ s/!key!/$key_name/;
		
		my $erflg;
		for my $err (@err) {
			if ($err eq $key) {
				$erflg++;
				last;
			}
		}
		# 入力なし
		if ($erflg) {
			$tmp =~ s|!val!|<span class="msg">$key_nameは入力必須です.</span>|;
		
		# 正常
		} else {
			$$in{$key} =~ s/\t/<br>/g;
			$tmp =~ s/!val!/$$in{$key}/;
		}
		print $tmp;
		
		$bef = $key;
	}
	
	# フッタ
	print $foot;
	exit;
}

#-----------------------------------------------------------
#  フォームデコード
#-----------------------------------------------------------
sub parse_form {
	my (@key,@need,%in);
	for my $key ( $cgi->param() ) {
		
		# 複数値の場合はスペースで区切る
		my $val = join(" ", $cgi->param($key));
		
		# 無害化/改行変換
		$key =~ s/[<>&"'\r\n]//g;
		$val =~ s/&/&amp;/g;
		$val =~ s/</&lt;/g;
		$val =~ s/>/&gt;/g;
		$val =~ s/"/&quot;/g;
		$val =~ s/'/&#39;/g;
		$val =~ s/\r\n/\t/g;
		$val =~ s/\r/\t/g;
		$val =~ s/\n/\t/g;
		
		# 入力必須
		if ($key =~ /^_(.+)/) {
			$key = $1;
			push(@need,$key);
		}
		
		# 受け取るキーの順番を覚えておく
		push(@key,$key);
		
		# %inハッシュに代入
		$in{$key} = $val;
	}
	
	# post送信チェック
	if ($cf{postonly} && $ENV{REQUEST_METHOD} ne 'POST') {
		error("不正なアクセスです");
	}
	
	# リファレンスで返す
	return (\@key,\@need,\%in);
}

#-----------------------------------------------------------
#  フッター
#-----------------------------------------------------------
sub footer {
	my $foot = shift;
	
	# 著作権表記（削除・改変禁止）
	my $copy = <<EOM;
<p style="margin-top:2em;text-align:center;font-family:Verdana,Helvetica,Arial;font-size:10px;">
	- <a href="http://www.kent-web.com/" target="_top">POST MAIL</a> -
</p>
EOM

	if ($foot =~ /(.+)(<\/body[^>]*>.*)/si) {
		print "$1$copy$2\n";
	} else {
		print "$foot$copy\n";
		print "</body></html>\n";
	}
	exit;
}

#-----------------------------------------------------------
#  エラー処理
#-----------------------------------------------------------
sub error {
	my $err = shift;
	
	open(IN,"$cf{tmpldir}/error.html") or die;
	my $tmpl = join('',<IN>);
	close(IN);
	
	# 文字置き換え
	$tmpl =~ s/!key!/エラー内容/g;
	$tmpl =~ s|!val!|<span class="msg">$err</span>|g;
	
	print "Content-type: text/html; charset=utf-8\n\n";
	print $tmpl;
	exit;
}

#-----------------------------------------------------------
#  時間取得
#-----------------------------------------------------------
sub get_time {
	$ENV{TZ} = "JST-9";
	my ($sec,$min,$hour,$mday,$mon,$year,$wday) = localtime(time);
	my @week  = qw|Sun Mon Tue Wed Thu Fri Sat|;
	my @month = qw|Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec|;
	
	# 日時のフォーマット
	my $date1 = sprintf("%04d/%02d/%02d(%s) %02d:%02d:%02d",
			$year+1900,$mon+1,$mday,$week[$wday],$hour,$min,$sec);
	my $date2 = sprintf("%s, %02d %s %04d %02d:%02d:%02d",
			$week[$wday],$mday,$month[$mon],$year+1900,$hour,$min,$sec) . " +0900";
	
	return ($date1,$date2);
}

#-----------------------------------------------------------
#  ホスト名取得
#-----------------------------------------------------------
sub get_host {
	# ホスト名取得
	my $host = $ENV{REMOTE_HOST};
	my $addr = $ENV{REMOTE_ADDR};
	
	if ($cf{gethostbyaddr} && ($host eq "" || $host eq $addr)) {
		$host = gethostbyaddr(pack("C4", split(/\./, $addr)), 2);
	}
	$host ||= $addr;
	
	# チェック
	if ($cf{denyhost}) {
		my $flg;
		for ( split(/\s+/,$cf{denyhost}) ) {
			s/\./\\\./g;
			s/\*/\.\*/g;
			
			if ($host =~ /$_/i) { $flg++; last; }
		}
		if ($flg) { error("アクセスを許可されていません"); }
	}
	
	return ($host,$addr);
}

#-----------------------------------------------------------
#  送信チェック
#-----------------------------------------------------------
sub check_post {
	my $job = shift;
	
	# 時間取得
	my $now = time;
	
	# ログオープン
	open(DAT,"+< $cf{datadir}/log.dat") or error("open err: log.dat");
	eval "flock(DAT,2);";
	my $log = <DAT>;
	
	# 分解
	my ($ip,$time) = split(/<>/,$log);
	
	# IP及び時間をチェック
	if ($ip eq $addr && $now - $time <= $cf{block_post}) {
		close(DAT);
		error("連続送信は$cf{block_post}秒間お待ちください");
	}
	
	# 送信時は保存
	if ($job eq "send") {
		seek(DAT,0,0);
		print DAT "$addr<>$now";
		truncate(DAT,tell(DAT));
	}
	close(DAT);
}

#-----------------------------------------------------------
#  電子メール書式チェック
#-----------------------------------------------------------
sub check_email {
	my ($eml) = @_;
	
	# E-mail書式チェック
	if ($eml =~ /\,/) {
		error("メールアドレスにコンマ ( , ) が含まれています");
	}
	if ($eml ne '' && $eml !~ /^[\w\.\-]+\@[\w\.\-]+\.[a-zA-Z]{2,6}$/) {
		error("メールアドレスの書式が不正です");
	}
}

#-----------------------------------------------------------
#  禁止ワードチェック
#-----------------------------------------------------------
sub check_word {
	my $flg;
	for (@$key) {
		for my $wd ( split(/,/,$cf{no_wd}) ) {
			if (index($$in{$_},$wd) >= 0) {
				$flg++;
				last;
			}
		}
		if ($flg) { error("禁止ワードが含まれています"); }
	}
}

#-----------------------------------------------------------
#  mimeエンコード
#  [quote] http://www.din.or.jp/~ohzaki/perl.htm#JP_Base64
#-----------------------------------------------------------
sub mime_unstructured_header {
  my $oldheader = shift;
  jcode::convert(\$oldheader,'euc','utf8');
  my ($header,@words,@wordstmp,$i);
  my $crlf = $oldheader =~ /\n$/;
  $oldheader =~ s/\s+$//;
  @wordstmp = split /\s+/, $oldheader;
  for ($i = 0; $i < $#wordstmp; $i++) {
    if ($wordstmp[$i] !~ /^[\x21-\x7E]+$/ and
	$wordstmp[$i + 1] !~ /^[\x21-\x7E]+$/) {
      $wordstmp[$i + 1] = "$wordstmp[$i] $wordstmp[$i + 1]";
    } else {
      push(@words, $wordstmp[$i]);
    }
  }
  push(@words, $wordstmp[-1]);
  foreach my $word (@words) {
    if ($word =~ /^[\x21-\x7E]+$/) {
      $header =~ /(?:.*\n)*(.*)/;
      if (length($1) + length($word) > 76) {
	$header .= "\n $word";
      } else {
	$header .= $word;
      }
    } else {
      $header = add_encoded_word($word, $header);
    }
    $header =~ /(?:.*\n)*(.*)/;
    if (length($1) == 76) {
      $header .= "\n ";
    } else {
      $header .= ' ';
    }
  }
  $header =~ s/\n? $//mg;
  $crlf ? "$header\n" : $header;
}
sub add_encoded_word {
  my ($str, $line) = @_;
  my $result;
  my $ascii = '[\x00-\x7F]';
  my $twoBytes = '[\x8E\xA1-\xFE][\xA1-\xFE]';
  my $threeBytes = '\x8F[\xA1-\xFE][\xA1-\xFE]';
  while (length($str)) {
    my $target = $str;
    $str = '';
    if (length($line) + 22 +
	($target =~ /^(?:$twoBytes|$threeBytes)/o) * 8 > 76) {
      $line =~ s/[ \t\n\r]*$/\n/;
      $result .= $line;
      $line = ' ';
    }
    while (1) {
      my $encoded = '=?ISO-2022-JP?B?' .
      b64encode(jcode::jis($target, 'euc', 'z')) . '?=';
      if (length($encoded) + length($line) > 76) {
	    $target =~ s/($threeBytes|$twoBytes|$ascii)$//o;
	    $str = $1 . $str;
      } else {
	    $line .= $encoded;
	    last;
      }
    }
  }
  $result . $line;
}
# [quote] http://www.tohoho-web.com/perl/encode.htm
sub b64encode {
    my $buf = shift;
    my ($mode,$tmp,$ret);
    my $b64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                . "abcdefghijklmnopqrstuvwxyz"
                . "0123456789+/";

    $mode = length($buf) % 3;
    if ($mode == 1) { $buf .= "\0\0"; }
    if ($mode == 2) { $buf .= "\0"; }
    $buf =~ s/(...)/{
        $tmp = unpack("B*", $1);
        $tmp =~ s|(......)|substr($b64, ord(pack("B*", "00$1")), 1)|eg;
        $ret .= $tmp;
    }/eg;
    if ($mode == 1) { $ret =~ s/..$/==/; }
    if ($mode == 2) { $ret =~ s/.$/=/; }
    
    return $ret;
}

#-----------------------------------------------------------
#  Base64エンコード
#-----------------------------------------------------------
sub conv_b64 {
	my $str = shift;
	
	$str =~ s/\n/\r\n/g;
	return base64::b64encode($str);
}

#-----------------------------------------------------------
#  セッションディレクトリ掃除
#-----------------------------------------------------------
sub ses_clean {
	my $time = time;
	
	opendir(DIR,"$cf{datadir}/ses");
	while( my $dir = readdir(DIR) ) {
		next if ($dir eq '.');
		next if ($dir eq '..');
		next if ($dir eq 'index.html');
		
		# ファイル時間取得
		my $mtime = (stat("$cf{datadir}/ses/$dir"))[9];
		
		# 1時間以上経過しているファイルは削除
		unlink("$cf{datadir}/ses/$dir") if ($time - $mtime > 3600);
	}
	closedir(DIR);
}

