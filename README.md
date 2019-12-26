# jupter_auth_mysql
mysql authenticator for jupyterhub on kubernetes

## JupyterHub Authentication

Jupyerhub初始的auth type是dummy, 就是个伪认证，输任意密码就能登录(可以通过修改config.yaml的auth:dummy:password改掉)，此外还支持OAuth2、LDAP的方式，可以通过GitHub、google、CILogon等账号认证，这些配置方式在[官方文档](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/authentication.html)介绍的还蛮详细的。基于常见数据库进行身份验证的官方资料没找到，网上找了一些博客，写了个mysql账号密码认证的模块加到镜像里去。

## mysqauthenticator包
写一个mysqlauthenticator的py包，大致功能就是连接数据库验证账号密码的常规操作。[具体代码](https://github.com/wenxinax/jupter_auth_mysql)
```python
class MysqlAuthenticator(Authenticator):

	"""JupyterHub Authenticator Based on Mysql"""

	def __init__(self, **kwargs):
		super(MysqlAuthenticator, self).__init__(**kwargs)

	@gen.coroutine
	def authenticate(self, handler, data):

		db_url = "mysql+mysqlconnector://root:root@192.168.199.182:3306/jupyter"
		session = init(db_url)

		username = data['username']
		passwd = data['password']

		try:
			user = session.query(User).filter(User.username == username).filter(User.password == passwd).one()
			if user is not None:
				return user.username
			else:
				return None
		except:
			return None
 ```           
 还要建一个mysql的服务，我直接开了个docker，建jupyter数据库，建user表，`id` `username` `password`三个字段。插入一些测试数据。

 ## 制作新的镜像
 原来的Dockerfile我还没研究，就直接在原有的容器里加入新的内容，然后再commit成新的镜像。
 ```shell
 # 首先启动jupyterhub服务
 # 在k8s-hub容器运行的节点，进入容器先安装一些依赖的模块
 docker exec -it 6db8b54b25b8 bash
 # 安装wheel、sqlalchemy、mysql-connector
 pip3 install wheel
 pip3 install sqlalchemy
 pip3 install mysql-connector

 # 退出容器，把mysqlauthenticator包拷贝到pip3的下载目录
 # 注意路径，要不然import不进去。在容器里是/home/jovyan/.local/lib/python3.6/site-packages/
 docker cp /root/myspace/workspace/jupyter/jupter_auth_mysql/mysqlauthenticator 6db8b54b25b8:/home/jovyan/.local/lib/python3.6/site-packages/

# 打tag 这里我传到自己搭建的docker仓库里去，方便其他机子pull
docker tag 6db8b54b25b8 192.168.199.182:5000/jupyterhub/k8s-hub:v0.1.0
# push
docker push 192.168.199.182:5000/jupyterhub/k8s-hub:v0.1.0
```

## 修改config.yaml
首先把hub的镜像改掉
```yaml
hub:
  image:
    name: 192.168.199.182:5000/jupyterhub/k8s-hub
    tag: v0.1.0
```
然后改掉auth， 一处是改auth:type为custom，然后配置custom的class，这样源码里就会import上面的mysqlauthenticator.MysqlAuthenticator这个类。我还配了一个admin权限的user，这个admin user的控制面板会有一个简单的管理页面。
```yaml
auth:
  type: custom
  custom: 
    className: mysqlauthenticator.MysqlAuthenticator
  whitelist:
    users:
  admin:
    access: true
    users:
      - wenxinax
```

然后重启一下jupyterhub服务就行了。输入的账号密码没有通过数据库验证的话提示 Invalid username or password 就算成功了。
