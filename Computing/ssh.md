SSHはリモート環境のシェルを安全にローカル環境から実行する.また,SSHが提供するポートフォワーディングによってリモート環境のポートをローカル環境のポートとトンネルで接続することで,ローカル環境のブラウザからリモート環境のJupyterサーバーなどに接続することができる.
ここでは，研究室内のサーバ(以後サーバ，ipアドレス192.168.1.256)にアカウントを作成し，SSH接続する方法を説明する．
新規に接続する人をAlice，すでにサーバにアカウントを持っている人をBobとする．

# 0. ユーザーアカウント作成
Bobはサーバーにログインし，Aliceのアカウントを作成する．仮にAliceのアカウント名をalice.alexanderとする．
```
sudo adduser alice.alexander # アカウント作成
sudo passwd alice.alexander karipasu # 仮のパスワード(karipasu)を付与
```
Bobの出番はここまでで，以後はすべてAliceは行う．

# 1. 初回ログイン
AliceはSSHでサーバーに接続する．
```
ssh alice.alexander@192.168.1.256 # パスワードを問われるので，karipasuを使ってログインする．
passwd # 自分のパスワードを設定する．まず現在のパスワードを入力し，次に自分の考えたパスワードを入力する．
```

# 2. SSH鍵設定
[SSH公開鍵認証で接続するまで](https://qiita.com/kazokmr/items/754169cfa996b24fcbf5) を参考に鍵ペアを作成し，公開鍵をサーバーに転送する．
Aliceの.ssh/configファイルは以下のようになる．
```.ssh/config
Host server
  HostName 192.168.1.256
  User alice.alexander
  IdentityFile ~/.ssh/id_ed25519
```

# 3. ポートフォワーディング設定
各ユーザは特定の[ポート](https://wa3.i-3-i.info/word1774.html)を用いてサーバ上のjupyterにアクセスする．
ポートフォワーディングはローカルのポートとサーバのポートを同一視させるSSHの機能であり，これによってローカルのブラウザからサーバ上のjupyter notebookにアクセスできる．
AliceとBobに割り当てられたポートがそれぞれ10001~10010, 10011~10020とすると，Aliceの```.ssh/config```を以下のように編集することでssh serverするときに自動的にポートフォワーディングが行われる．
```.ssh/config
Host server
  HostName 192.168.1.256
  User alice.alexander
  IdentityFile ~/.ssh/id_ed25519
```


![Untitled Diagram drawio](https://github.com/user-attachments/assets/420a7a2b-ebee-4086-87c5-775a85d47d84)
