研究室のVPNに接続する方法を説明する．東大のVPNとは異なるので注意すること．
ゲートウェイなど秘匿すべき情報はslackに記載している．

# Windows

# Mac

# Linux (ubuntu 22.04)
1. https://qiita.com/maromaro0013/items/86f129a953dbe7419e56 を参考にkl2tpdをインストールする.  
libnm-gtk-dev libnm-util-dev libnm-glib-vpn-dev は不要なので無視する.


3. 画像のように設定する.

![fig1](https://github.com/user-attachments/assets/6fe2c60f-a6a6-4711-aa1f-f57e1a1e9ebf)  

![image](https://github.com/user-attachments/assets/004cc1bb-008a-4b97-92b0-da44a143327b)  
Phase1 Algorithms: 3des-sha1-modp1024  
Pahse2 Algorithms: aes256-sha1,aes128-sha1,3des-sha1!
![image](https://github.com/user-attachments/assets/13b8d1d2-5369-4e79-8df7-0f1b0d309509)  


論文誌のウェブサイトなどにアクセスすると，東大経由で接続していることは検知してくれるけど，なぜか論文のダウロードができないサイトがある(IEEEなど)．
東大のVPNを使うこと．

![image](https://github.com/user-attachments/assets/4c2cdd8b-1835-43cb-bd09-d20122127d21)


添付画像のようにすると，192.168.1.14や192.168.1.171のサーバーにのみVPN経由でアクセスし，別のipには自宅の環境から直接アクセスする．
大学当局に見られたくない通信をするときなど
