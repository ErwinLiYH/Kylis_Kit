"""
This is a multithreading m3u8 download module. Support download m3u8 file and convert it to mp4. Support resume download.

Example:

```python
#test.py
downloader = mder.m3u8_downloader(m3u8_file_path='./test.m3u8',temp_file_path='./',mp4_path='./test.mp4',num_of_threads=10)
# parameters
# 1.m3u8_file_path
# default : no default   (type : str)
# 2.temp_file_path
# default : '.'          (type : str)
# 3.mp4_path
# default : './test.mp4' (type : str)
# 4.num_of_threads
# default : 10           (type : int)

downloader.start()
# parameters
# 1.mod
# default : 0            (type : int)
# mod 0 means delete TS folder and m3u8 file if download completely
# mod 1 means delete m3u8 file only if download completely
# mod 2 means delete TS folder only if download completely
# mod 3 means reserve TS folder and m3u8 file if download completely
# 2.time_out
# default : 60           (type : int)(units : seconds)
# The time_out is the timeout in request.get(timeout=)
```

**before download**

the structure of ./ is:
```
.
├── test.m3u8
└── test.py
```

**when it is downloading**

the structure of ./ is:
```
.
├── TS
│   ├── qzCFnDUZE9_720_5308_0000.ts
│   ├── qzCFnDUZE9_720_5308_0001.ts
│   ├── qzCFnDUZE9_720_5308_0002.ts
│   ├── qzCFnDUZE9_720_5308_0003.ts
│   ├── qzCFnDUZE9_720_5308_0004.ts
│   ├── qzCFnDUZE9_720_5308_0005.ts
│   ├── qzCFnDUZE9_720_5308_0006.ts
│   ├── qzCFnDUZE9_720_5308_0007.ts
│   ├── qzCFnDUZE9_720_5308_0008.ts
│   ├── qzCFnDUZE9_720_5308_0009.ts
│   └── qzCFnDUZE9_720_5308_0010.ts  
├── test.m3u8
└── test.py
```
process bar:  <<\*>>  29% 500/1752 [01:33<04:02] <<\*>> 

TS is temp folder, all .ts file are in it. The path of it is %temp_file_path%/TS, in the test case, it is in ./TS. If the mission is not complete, the m3u8 file and TS folder will be reserved, you can instance a new downloader with corresponding TS folder and m3u8 file, and use the start() function to begin, in this way, the mission will go on.

**after download and download successfully**

the structure of ./ is:
```
.
├── test.mp4
└── test.py
```

If some .ts download failed, the module will redownload for 3 times, and the information will print to the command line

at last, the command line is like this:
```
<<*>>  99% 1737/1752 [05:35<00:22] <<*>>
thread0 Time out ERROR qzCFnDUZE9_720_5308_1710.ts
thread2 Time out ERROR qzCFnDUZE9_720_5308_1722.ts
thread0 redownload successfully qzCFnDUZE9_720_5308_1710.ts
<<*>>  99% 1738/1752 [06:20<03:19] <<*>>
thread2 redownload successfully qzCFnDUZE9_720_5308_1722.ts
<<*>> 100% 1752/1752 [06:26<00:00] <<*>>
downloading finished 100.00%
```
**restart**
If you want to restart a incomplete mission, you only should use the corresponding TS folder and .m3u8 file

"""

# a multithreading m3u8 download module and the number of threads can decide by yourself
# author: walkureHHH
# last modify: 2020/06/17
import requests
from urllib.parse import urljoin
from threading import Thread
from threading import Lock
import os
import shutil
from tqdm import tqdm


class thread_num_ERROR(Exception):
    """
    Thread number error.
    Be raised when the number of threads is eqial to smaller than 0.
    """
    pass

class mod_ERROR(Exception):
    """
    Mod error.
    Be raised when the mod is not in [0,1,2,3].
    """
    pass

class m3u8_downloader:
    """
    M3u8 downloader.
    """
    temp_file_path = ''
    """@private"""
    mp4_path = ''
    """@private"""
    num_of_threads = ''
    """@private"""
    m3u8_file_path = ''
    """@private"""
    urls = []
    """@private"""
    names = []
    """@private"""
    has_download_name = []
    """@private"""
    cant_dow = []
    """@private"""
    total = 0
    """@private"""
    lock = Lock()
    """@private"""
    def __init__(self,m3u8_file_path, url_prefix=None,temp_file_path='.',mp4_path='./test.mp4',num_of_threads=10):
        """
        Initialize the m3u8 downloader.

        Parameters
        ----------
        m3u8_file_path : str
            The path of the m3u8 file.
        url_prefix : str
            The prefix of the url. Default is None.
            Some m3u8 file has not the full url, so you can add the prefix to the url.
            For example, the url is '/video/1.ts', and the prefix is 'http://www.example.com'.
        temp_file_path : str
            The path of the temporary folder (store *.ts files). Default is '.'.
        mp4_path : str
            The path of the result mp4 file. Default is './test.mp4'.
        num_of_threads : int
            The number of threads. Default is 10.

        """
        if num_of_threads <= 0:
            raise thread_num_ERROR('the number of threads can\'t smaller than 0')
        self.mp4_path = mp4_path
        self.temp_file_path = temp_file_path 
        self.num_of_threads = num_of_threads
        self.m3u8_file_path = m3u8_file_path
        if os.path.exists(self.temp_file_path+'/TS'):
            print("""warning: the temporary folder has exited\n 
please comfirm the temporary folder included the fragment video you need""")
            self.has_download_name = os.listdir(self.temp_file_path+'/TS')
        else:
            os.mkdir(self.temp_file_path+'/TS')
            self.has_download_name = []
        with open(self.m3u8_file_path,'r') as m3u8:
            temp_url = [m3u8_lines.replace('\n','') for m3u8_lines in m3u8.readlines() if m3u8_lines.startswith('#')==False]
        if url_prefix != None:
            temp_url = [urljoin(url_prefix, i) for i in temp_url]
        self.total = len(temp_url)
        self.names = [i.split('/')[-1].split('?')[0] for i in temp_url]
        self.urls = [[] for j in range(0, self.num_of_threads)]
        for index, el in enumerate(temp_url):
            self.urls[index%self.num_of_threads].append(el)
        return
    
    def start(self,mod = 0, time_out = 60):
        """
        Start download.

        Parameters
        ----------
        mod : int
            The mod of the download. Default is 0.
            0: delete the m3u8 file and the temporary folder.
            1: delete the m3u8 file.
            2: delete the temporary folder.
            3: do nothing.
        time_out : int
            The time out of the download. Default is 60s.
        """
        if mod not in [0,1,2,3]:
            raise mod_ERROR('Only have mod 0 , 1 , 2 or 3')
        with tqdm(total=self.total,bar_format='<<*>> {percentage:3.0f}% {n_fmt}/{total_fmt} [{elapsed}<{remaining}] <<*>> ') as jdt:
            Threads = []
            for i in range(self.num_of_threads):
                thread = Thread(target=self.__download, args=(self.urls[i],'thread'+str(i),jdt,time_out))
                Threads.append(thread)
            for threads in Threads:
                threads.start()
            for threads in Threads:
                threads.join()
        percent = '%.02f%%'%((len(self.has_download_name)/len(self.names))*100)
        if len(self.has_download_name)==len(self.names):
            print('downloading finished',percent)
            for names in self.names:
                ts = open(self.temp_file_path+'/TS/'+names,'rb')
                with open(self.mp4_path,'ab') as mp4:
                    mp4.write(ts.read())
                ts.close()
            if mod == 0 or mod == 1:
                os.remove(self.m3u8_file_path)
            if mod == 0 or mod == 2:
                shutil.rmtree(self.temp_file_path+'/TS')
        else:
            print('----------------------------------------------------------------')
            for cantdow_urls in self.cant_dow:
                print('downloading fail:',cantdow_urls)
            print('incomplete downloading',percent)

    def __download(self, download_list, thread_name, jdt, time_out):
        for urls in download_list:
            if urls.split('/')[-1].split('?')[0] not in self.has_download_name:
                for i in range(0,5):
                    try:
                        conn = requests.get(urls,timeout=time_out)
                        if conn.status_code == 200:
                            with open(self.temp_file_path+'/TS/'+urls.split('/')[-1].split('?')[0],'wb') as ts:
                                ts.write(conn.content)
                            with self.lock:
                                if i != 0:
                                    print('\n'+thread_name,'redownload successfully',urls.split('/')[-1].split('?')[0])
                                self.has_download_name.append(urls.split('/')[-1].split('?')[0])
                                jdt.update(1)
                            break
                        else:
                            with self.lock:
                                if i == 0:
                                    print('\n'+thread_name,conn.status_code,urls.split('/')[-1].split('?')[0],'begin retry 1')
                                else:
                                    print('\n'+thread_name,conn.status_code,urls.split('/')[-1].split('?')[0],'Retry '+ str(i) +'/3')
                                if i == 4:
                                    self.cant_dow.append(urls)
                    except:
                        with self.lock:
                            if i == 0:
                                print('\n'+thread_name,'Time out ERROR',urls.split('/')[-1].split('?')[0],'begin retry 1')
                            else:
                                print('\n'+thread_name,'Time out ERROR',urls.split('/')[-1].split('?')[0],'Retry '+ str(i) +'/3')
                            if i == 4:
                                self.cant_dow.append(urls)
            else:
                with self.lock:
                    jdt.update(1)
if __name__ == "__main__":
    a = m3u8_downloader('/mnt/c/Users/kylis/Downloads/r.m3u8',temp_file_path='.',mp4_path='./1.mp4', num_of_threads=17)
    a.start()
