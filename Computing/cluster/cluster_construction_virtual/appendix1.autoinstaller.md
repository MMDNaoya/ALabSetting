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

3. 自動インストール機能を追加したインストールメディア作成
  2.において全ての設定がうまくいくことを確認できたら，1本のusbメモリにOSのインストーラと自動インストール設定ファイルを入れる．

  (1) 準備

  ```
  sudo apt update
  sudo apt install -y xorriso isolinux
  ```
  
  (2) ubuntu isoを展開  
  作業用ディレクトリを作成し，ISOを展開
  ```
  mkdir -p ~/ubuntu-iso
  sudo mount -o loop ubuntu.iso /mnt
  rsync -a /mnt/ ~/ubuntu-iso/
  sudo umount /mnt
  ```

  (3) nocloudディレクトリを作成  
  ISO内の```nocloud```用設定ファイルを配置する
  ```
  mkdir -p ~/ubuntu-iso/nocloud/
  ```

  (4) ```ubuntu-iso/nocloud/```に```user-data```と```meta-data```を配置  
  (5) ```grub.cfg```を編集して```autoinstall```を有効化  
  - ```~/ubuntu-iso/boot/grub/grub.cfg``` の後に```autoinstall``のパラメターを追加
  - ```ds=nocloud\;s=/cdrom/nocloud/```によって，nocloud形式の設定ファイルを用いて，その設定ファイルは```/cdrom/nocloud/```の下にあることを指定する．
  ```
-linux	/casper/vmlinuz ---
+linux	/casper/vmlinuz --- nomodeset autoinstall ds=nocloud\;s=/cdrom/nocloud/
  ```

  (6)カスタムisoファイルを作成
  ```
  cd ~/ubuntu-iso

  xorriso -as mkisofs -D -r -V "Custom Ubuntu Server"     -J -joliet-long -b boot/grub/i386-pc/eltorito.img     -no-emul-boot -boot-load-size 4 -boot-info-table     -o ~/custom-ubuntu-server.iso .
  ```

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