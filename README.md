# working

工作中编写的一些程序

1. 分页类，基于 flask-sqlalchemy 的 Pagination 类修改，可以使用现有宏
2. 表单验证 js，基于 jQuery， 可以实现是否为空，是否为合法 Email 等验证，并在页面显示错误提示
3. JsonRPC，类似 Zabbix Api 的 JsonRPC 框架，实现了参数验证和自动加载模块
4. Graphite Carbon Client，通过 socket 连接发送数据至 Graphite Carbon Daemon，支持批量发送
5. sysinfo.py 系统信息收集脚本，可以收集 CPU，内存，硬盘，网卡，制造商，型号，软件版本等系统信息
6. Web 存储程序，基于 flask 和 flask-sqlalchemy，文件存储采用 FastFS，实现了很多功能，但是方式并不是很好
7. md5.sh，传入一个目录，可以递归的计算目录下所有文件的 md5 值，判断目录是否为空的方式并不是很好，用 Bash 实现递归很有意思
8. ansible_callback.py，ansible callback 示例，定义 CallbackModule 类，并定义类似 runner_on_ok 这样函数，在函数内部进行自定操作
