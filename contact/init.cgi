# モジュール宣言/変数初期化
use strict;
my %cf;
#┌─────────────────────────────────
#│ POST-MAIL : postmail.cgi - 2005/08/11
#│ copyright (c) kentweb, 1997-2025
#│ http://www.kent-web.com/
#└─────────────────────────────────
$cf{version} = 'postmail v10.0';
#┌─────────────────────────────────
#│ [注意事項]
#│ 1. このプログラムはフリーソフトです。このプログラムを使用した
#│    いかなる損害に対して作者は一切の責任を負いません。
#│ 2. 送信フォームのHTMLページの作成に関しては、HTML文法の範疇
#│    となるため、サポート対象外となります。
#│ 3. 設置に関する質問はサポート掲示板にお願いいたします。
#│    直接メールによる質問はお受けいたしておりません。
#└─────────────────────────────────
#
# [ 送信フォーム (HTML) の記述例 ]
#
# ・タグの記述例 (1)
#   おなまえ <input type="text" name="name">
#   → このフォームに「山田太郎」と入力して送信すると、
#      「name} = 山田太郎」という形式で受信します
#
# ・タグの記述例 (2)
#   お好きな色 <input type="radio" name="color" value="青">
#   → このラジオボックスにチェックして送信すると、
#      「color} = 青」という形式で受信します
#
# ・タグの記述例 (3)
#   E-mail <input type="text" name="email">
#   → name値に「email」という文字を使うとこれはメールアドレス
#      と認識し、アドレスの書式を簡易チェックします
#   → (○) abc@xxx.co.jp
#   → (×) abc.xxx.co.jp → 入力エラーとなります
#
# ・タグの記述例 (4)
#   E-mail <input type="text" name="_email">
#   → name値の先頭に「アンダーバー 」を付けると、その入力値は
#     「入力必須」となります。
#      上記の例では、「メールアドレスは入力必須」となります。
#
# ・name値への「全角文字」の使用は可能です
#  (例) <input type="radio" name="年齢" value="20歳代">
#  → 上記のラジオボックスにチェックを入れて送信すると、
#     「年齢} = 20歳代」という書式で受け取ることができます。
#
# ・name値を「name」とするとこれを「送信者名」と認識して送信元の
#   メールアドレスを「送信者 <メールアドレス>」というフォーマットに
#   自動変換します。
#  (フォーム記述例)  <input type="text" name="name">
#  (送信元アドレス)  太郎 <taro@email.xx.jp>
#
# ・制御タグ-1
#   → 入力必須項目を強制指定する（半角スペースで複数指定可）
#   → ラジオボタン、チェックボックス対策
#   → name値を「need」、value値を「必須項目1 + 半角スペース +必須項目2 + 半角スペース ...」
#   (例) <input type="hidden" name="need" value="名前 メールアドレス 性別">
#
# ・制御タグ-2
#   → 2つの入力内容が同一かをチェックする
#   → name値を「match」、value値を「項目1 + 半角スペース + 項目2」
#   (例) <input type="hidden" name="match" value="email email2">
#
# ・制御タグ-3
#   → name値の並び順を指定する（半角スペースで複数指定）
#   → 入力エラー画面及びメール本文の並びを指定します
#   (例) <input type="hidden" name="sort" value="name email メッセージ">

#===========================================================
#  ▼基本設定
#===========================================================

# 送信先メールアドレス
$cf{mailto} = 'information@pls-net.co.jp';

# sendmailのパス【サーバパス】
# → プロバイダの指定を確認のこと
$cf{sendmail} = '/usr/sbin/sendmail';

# sendmailへの-fコマンド（プロバイダの仕様確認）
# 0 : no
# 1 : yes
$cf{send_fcmd} = 1;

# メール本文をBase64で送る
# → 機種依存文字等を扱う場合や、UTF-8版で海外との送信時に有効。
# 0 : no
# 1 : yes
$cf{send_b64} = 1;

# フォームのname値の置き換えをする場合（任意オプション）
# → 英字のname値を日本語に自動的に置き換えます。
# 例: 「email = xx@xx.xx」→「メールアドレス = xx@xx.xx」
$cf{replace} = {
		'name'    => 'お名前',
		'email'   => 'メールアドレス',
		'comment' => 'コメント',
	};

# 送信者へのメール返信
# 0 : no
# 1 : yes
$cf{auto_res} = 1;

# メール件名
$cf{subject} = 'お問い合わせフォーム';

# 返信向けメールタイトル
$cf{sub_reply} = 'お問い合わせありがとうございます';

# 本体プログラム【URLパス】
$cf{mail_cgi} = './postmail.cgi';

# データディレクトリ【サーバパス】
$cf{datadir} = './data';

# テンプレートディレクトリ【サーバパス】
$cf{tmpldir} = './tmpl';

# 送信後の形態
# 0 : 完了メッセージを出す.
# 1 : 戻り先 ($back) へ自動ジャンプさせる.
$cf{reload} = 0;

# 送信後の戻り先【URLパス】
$cf{back} = '../index.html';

# 同一IPアドレスからの連続送信制御
# → 許可する間隔を秒数で指定（0にするとこの機能は無効）
$cf{block_post} = 60;

# 送信は method=POST 限定 (セキュリティ対策)
# 0 : no
# 1 : yes
$cf{postonly} = 1;

# 最大受信サイズ（Byte）
# → 例 : 102400Bytes = 100KB
$cf{maxdata} = 102400;

# ホスト名取得方法
# 0 : gethostbyaddr関数を使わない
# 1 : gethostbyaddr関数を使う
$cf{gethostbyaddr} = 0;

# アクセス制限（複数あれば半角スペースで区切る、アスタリスク可）
# → 拒否ホスト名又はIPアドレスの記述例
#   （前方一致は先頭に ^ をつける）【例】^210.12.345.*
#   （後方一致は末尾に $ をつける）【例】*.anonymizer.com$
$cf{denyhost} = '';

# 禁止ワード
# → 投稿時禁止するワードをコンマで区切る
$cf{no_wd} = '';

# ----- reCapcha v3 使用時の設定
# Google reCaptchaの事前登録が必要
# https://www.google.com/recaptcha/about/
# 0 : 使用しない
# 1 : 使用する
$cf{recaptcha} = 0;

# スコア許可基準
# 0.0～1.0のスコアのうち（それ以上）許可する値
$cf{recap_score} = 0.5;

# サイトキー
$cf{site_key} = '';

# シークレットキー
$cf{secret_key} = '';

# フォームAPI定義
$cf{gr_api} = <<EOM;
<script src="https://www.google.com/recaptcha/api.js?render=$cf{site_key}"></script>
EOM

# フォームサイトキー送信定義
$cf{gr_key} = <<EOM;
<script>
grecaptcha.ready(function() {
	grecaptcha.execute('$cf{site_key}',{action:'submit'}).then(function(token) {
		document.getElementById('g-recaptcha-response').value=token;
	});
});
</script>
EOM

#===========================================================
#  ▲設定完了
#===========================================================

# 設定値を返す
sub set_init { return %cf; }


1;

