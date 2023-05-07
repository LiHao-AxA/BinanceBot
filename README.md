  一个币安量化机器人.  
  
  策略放在binance>quant_strategy文件下.
  
  [电报交流群](https://t.me/BinanceBot_Official)
  
  [注册币安](https://accounts.binance.com/register?ref=10036213)
  
  ## 使用Supervisor守护进程
  
  安装Supervisor 
  
  ```
  sudo yum install epel-release
  sudo yum install supervisor
  
  ```
  
  Supervisor是一个常见的守护进程管理工具，可确保进程在服务器启动时启动，并在进程崩溃时重新启动。要使用Supervisor，请安装Supervisor并创建一个配置文件名为BinanceBot.err.log 
  
  ```
  [program:BinanceBot]
  command=/usr/bin/python3 /usr/local/lib/python3.11/site-packages/binance/quant_strategy/InfiniteGrid.py
  directory=/usr/local/lib/python3.11/site-packages/binance/quant_strategy/
  autostart=true
  autorestart=true
  stderr_logfile=/usr/local/lib/python3.11/site-packages/binance/quant_strategy/BinanceBot.err.log
  stdout_logfile=/usr/local/lib/python3.11/site-packages/binance/quant_strategy/BinanceBot.out.log
  ```
  
  新建文件存放到/usr/bin/python3 /usr/local/lib/python3.11/site-packages/binance/quant_strategy/目录下
  
  ## 使用systemd服务
  
  systemd是另一个守护进程管理工具，可以让你在服务器启动时自动启动进程。要使用systemd，请创建一个名为"BinanceBot.service"的文件
  
  ```
  [Unit]
  Description=BinanceBot
  After=network.target

  [Service]
  User=root
  WorkingDirectory=/usr/local/lib/python3.11/site-packages/binance/quant_strategy/
  ExecStart=/usr/bin/python3 /usr/local/lib/python3.11/site-packages/binance/quant_strategy/InfiniteGrid.py
  Restart=always
  RestartSec=3

  [Install]
  WantedBy=multi-user.target
  ```

  ### 然后，将文件保存到"/etc/systemd/system"目录中，并运行以下命令：
  
  ```
  systemctl daemon-reload
  systemctl start BinanceBot.service
  systemctl enable BinanceBot.service
  ```
  
  ## 使用crontab
  
  使用crontab来在服务器启动时自动启动进程。要使用crontab，请运行以下命令：
  
  ```
  crontab -e
  ```
  
  ## 将以下行添加到文件的末尾：
  
  ```
  @reboot nohup python3 /usr/local/lib/python3.11/site-packages/binance/quant_strategy/InfiniteGrid.py > output.log 2>&1 &
  ```
  
  将在服务器启动时自动运行你的Python程序，并将输出重定向到"output.log"文件中

