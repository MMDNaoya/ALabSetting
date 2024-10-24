[Jupyter](https://jupyter.org/)はJupyterはインタラクティブな計算環境を提供するオープンソースのウェブアプリケーションで，Pythonなどのプログラミング言語でコードを記述，実行，可視化できる．  
ここではサーバー上でJupyterを起動し，ローカルから接続する方法を説明する．

# Jupyter設定
複数ユーザが同一のサーバで[Jupyter](https://jupyter.org/)を走らせるとき，Jupyter Hubを使う方法と，各ユーザが別々にJupyterを走らせる方法がある．  
いまのところ利用者が少ないため，後者の方法を取る．人数の増加によりポートや計算資源の分配に問題が生じ始めたら，Jupyter Hubの利用を検討する．
ユーザは自分に割り当てられたポートをjupyterの通信ポートとして指定してjupyterを起動し，そのポートをローカルにフォワーディングしてローカルから接続する(Fig. 1)．

![Untitled Diagram drawio(1)](https://github.com/user-attachments/assets/85bac0bb-7fa0-4de3-9e1d-af6f6cab59c3)  
Figure １. ユーザごとにJupyterを起動して接続する

# Jupyter起動
## screenに入る
サーバにssh接続してJupyterを起動するのだが，ssh接続が切断されるとJupyterも強制終了してしまう．wifiの不調でsshが切断されたり，外出先で長時間かかる計算を行えないなどの不都合がある．  
[screenコマンド](https://qiita.com/hnishi/items/3190f2901f88e2594a5f)によってこの問題を解決する．  
screenをデタッチしたあとならば，ssh接続を切断した後もJupyterは動作し続ける．
サーバにssh接続し，```screen```[コマンド](https://qiita.com/hnishi/items/3190f2901f88e2594a5f)を実行する．

## Jupyter起動
Aliceに割り当てられたポート10001を指定し，Jupyterを起動する．
Jupyterのトップディレクトリは以下のコマンドではホームディレクトリ直下の```projects```というディレクトリだが，好みで変えて良い．
```
jupyter lab --port 10001 --NotebookApp.token='' --notebook-dir /home/alice.alexander/projects/ --no-browser --NotebookApp.password=''
```

## Screenを出る
Ctrl + a を打つことでscreenのセッションから出る．sshを切断してもJuputerは走り続ける．  
```screen -r```によってまたセッションに接続できる．

# Pythonパッケージマネージャ設定(省略可)
サーバにはすでにある程度pythonとpythonパッケージがインストールされているが，それらOSにインストールしたパッケージを利用するだけでは
- AliceはPyTorch 1.1，BobはPyTorch 1.2を使いたい
- AliceがあるプロジェクトではPyTorch 1.1，別のプロジェクトではPyTorch1.2を使いたい  
というような状況に対応できない．

そのため，各人が各プロジェクトでパッケージマネージャを利用して必要な環境を構築することを推奨する．  　
ここでは[Rye](https://rye.astral.sh/)を用いたパッケージマネージメントと，Jupyterでryeで作成した環境を利用する方法を説明する．

## rye環境作成
```
mkdir ./projects/myproject
cd ./projects/myproject
rye init --virtual --name myproject
```
によって，```./projects/myproject```にryeの環境が作成される．　　
rye addによってpythonパッケージを環境にインストールできる．
```rye add ipykernel```によって，Jupyterからこのrye環境をカーネルとして利用できるようにする．

## Jupyterでカーネルとして利用
ブラウザでjupyterに接続し，```myproject```に移動する．　　
New Launcher (Ctrl + Shilt + L) (左上の青地に白の＋ボタン)を押し，Pyproject Localでnotebookかconsoleを起動すると，作成したrye環境を利用できる．
![image](https://github.com/user-attachments/assets/55d6584f-ee9c-4d16-92a3-38395916c857)

この方法で作成したrye環境が複数存在すると，同じ名前で別々のrye環境カーネルが存在するようになるので注意すること．  
```rye run python -m ipykernel install --user --name=my_project --display-name "Python (Rye - my_project)"```
によってjupyterから見えるrye環境のカーネルの名前を指定できるらしい．
