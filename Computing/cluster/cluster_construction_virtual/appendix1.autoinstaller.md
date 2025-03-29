ubuntuのインストールを自動化するための方法を記す．

# インストール自動化方法概要
ubuntu serverのインストーラである```subiquity```に対してインストールの設定を記述した```user-data```ファイルを渡すことで，その設定に従って自動的にインストールさせる．．．のだと思う．[詳細](https://cloudinit.readthedocs.io/en/latest/reference/datasources/nocloud.html)  
```user-data```を渡すには，
- user-data # 設定ファイルそのもの
- meta-data # 空のファイル 

を準備し，インストーラを起動する．```user-data```作成，自動インストール機能を追加したインストールメディアを作成するために以下の手順を踏む．
1. 手動インストール
  ```1.install_ubuntu.md```ですでに扱った
2. 1の結果から```user-data```作成
  手動インストール後のOSにある```/var/log/installer/autoinstall-user-data```には手で入力した設定が```user-data```形式となって保存されている．これをもとにして自動インストーラの```user-data```を作成する．  
  特に```apt```のリポジトリ設定はややこしいので```/var/log/installer/autoinstall-user-data```からそのままコピーアンドペーストするとよい．  
  ```cloud-localds ./seed.iso user-data meta-data```によってこれらのファイルを```seed.iso```にまとめる．これをusbメモリに書き出し，ubuntuのインストールメディアとともに挿入してマシンを起動する． 
  インストールが失敗する場合．
  - Autoinstall ログ: /var/log/installer/subiquity-server-debug.log
  - cloud-initのログ: /var/log/cloud-init.log
  - curtinのログ: /var/log/installer/curtin-install.log
  
  などを見てデバッグする．

# 実際の設定の内容
## 設定の方針
ホスト名・ipアドレスはノードごとに異なるのだが，他の設定は全て同じであることを想定する．  
ホスト名・ipアドレスを```user-data```で指定することは可能なのだが，ノードごとにインストールメディアを書き換えるのは大変なので，
- ホスト名: autoinstall
- ipアドレス: 200.0.100.1

と固定し，インストール完了後にsshログインして固有のホスト名・ipアドレスに変更するようにする． インストール完了後には自動でシャットダウンするので，インストールメディアを抜いて起動し，ssh接続する．

最終的にできた```user-data```ファイルが```src/user-data```である．


# ノード個別の設定
```src```を```/share/installation```以下にコピーし  
```sudo src/configuration.py exclusive hostname ip```を実行する