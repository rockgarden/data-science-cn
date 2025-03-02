# 说明

[Getting started](https://pandas.pydata.org/docs/getting_started/index.html)

[User Guide](https://pandas.pydata.org/docs/user_guide/index.html)

[API reference](https://pandas.pydata.org/docs/reference/index.html)

[Development](https://pandas.pydata.org/docs/development/index.html)

[Code](https://github.com/pandas-dev/pandas)

参考：

- [ ] <https://www.jianshu.com/p/a9ea0a44988e>
- [ ] <https://blog.csdn.net/2301_81446229/article/details/139827723>
- [ ] <https://zhuanlan.zhihu.com/p/52312186>
- [ ] <https://zhuanlan.zhihu.com/p/650111510>
- [ ] <https://blog.csdn.net/m0_71838992/article/details/138419611>
- [ ] <https://blog.csdn.net/liumengqi11/article/details/113174269>
- [ ] <https://www.runoob.com/pandas/pandas-cleaning.html>
- [ ] <https://blog.csdn.net/m0_62283350/article/details/143113866>

## 数据速览

用于快速对数据进行探查的第三方包。

`pip install pandas-profiling`

安装完毕之后，直接导入使用即可

```py
import pandas as pd
import numpy as np
import os,pandas_profiling
os.chdir(r'D:\Data\Datas Analysis\learn\official\base\titanic')

datas = pd.read_csv('matt_train.csv',index_col=0)
pandas_profiling.ProfileReport(datas)
```
