

def waitNetworkReady(timeout: int = 60) -> tuple:
    """阻塞等待网络连接成功。

    @timeout： int，超时时间，范围1~3600秒，默认60秒。
    等待模组网络就绪。该方法会依次检测SIM卡状态、模组网络注册状态和PDP Context激活状态；
    在设定的超时时间之内，如果检测到PDP Context激活成功，会立即返回，否则直到超时才会退出。

    @return：返回一个元组，格式为：(stage, state)。
    stage，整型，表示当前正在检测什么状态：
    1表示正在检测SIM卡状态；
    2表示正在检测网络注册状态；
    3表示正在检测PDP Context激活状态。
    state，整型，根据stage值，来表示不同的状态，具体如下：
    1表示 SIM卡的状态，范围0-21，每个状态值的详细说明，请参考sim.getStatus()方法的返回值说明；
    2表示网络注册状态，范围0-11，每个状态值的详细说明，请参考net.getState()方法的返回值说明；
    3表示PDP Context激活状态，0表示没有激活成功，1表示激活成功。
    """
    ...
