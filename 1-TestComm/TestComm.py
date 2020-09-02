""" **************** zcanpro模块说明 ****************

# ZCANPRO程序中提供了zcanpro模块，使用"import zcanpro"导入至自定义的脚本中即可使用。

# 提供的接口如下：
1. buses = zcanpro.get_buses()
    获取ZCANPRO程序已经启动的总线信息(即打开的设备CAN通道)。
    * buses：为总线信息列表，如
    [
        {
            "busID": 101,       # 总线ID
            "devType": 1,       # 设备类型
            "devIndex": 0,      # 设备索引号
            "chnIndex": 0       # 通道索引号
        },
        ...
    ]

2. result, frms = zcanpro.receive(busID)
    获取指定总线的数据。
    * busID：指定总线ID, 整数类型
    * result：返回执行结果，整数类型，0-失败, 1-成功
    * frms: 返回获取的数据列表， 如
    [
        {
            "can_id": 101,              # 帧ID
            "is_canfd": 1,              # 是否为CANFD数据, 0-CAN, 1-CANFD
            "canfd_brs": 1,             # CANFD加速, 0-不加速, 1-加速
            "data": [0, 1, 2, 3, 4],    # 数据
            "timestamp_us": 666666      # 时间戳, 微妙
        },
        ...
    ]

3. result = zcanpro.transmit(busID, frms)
    发送数据至指定总线。
    * busID：指定总线ID, 整数类型
    * frms: 指定数据列表，同zcanpro.receive
    * result：返回执行结果, 整数类型，0-失败, 1-成功

4. zcanpro.write_log(msg)
    显示日志信息，ZCANPRO程序会在界面上显示该信息，便于跟踪脚本运行过程。
    * msg 日志信息，字符串类型

"""

""" **************** 扩展脚本文件编写说明 ****************

# 扩展脚本文件（即提供给ZCANPRO程序执行的脚本）必须提供以下接口供ZCANPRO程序调用。

1. z_main()
    入口函数，ZCANPRO程序运行扩展脚本时会首先调用该函数，该函数退出时即为扩展脚本运行结束。
    编写时，请注意不要让该函数执行死循环，确保其能正常运行结束，或者接收到ZCANPRO程序发送的停止运行命令后能正常退出。

2. z_notify(type, obj)
    事件通知函数，ZCANPRO程序会在产生相应事件的时候调用该接口通知运行的脚本。
    * type: 事件类型，字符串类型，目前支持的类型如下
        a) "stop": 停止脚本运行，接收到该命令后应让z_main函数立即运行结束。

"""

import os
import configparser
import time
import zcanpro

#--------------------------------------------------------class--------------------------------------------------------#
crcm32TableEx = \
[
	0x00000000, 0xf26b8303, 0xe13b70f7, 0x1350f3f4, 0xc79a971f, 0x35f1141c, 0x26a1e7e8, 0xd4ca64eb,
	0x8ad958cf, 0x78b2dbcc, 0x6be22838, 0x9989ab3b, 0x4d43cfd0, 0xbf284cd3, 0xac78bf27, 0x5e133c24,
	0x105ec76f, 0xe235446c, 0xf165b798, 0x030e349b, 0xd7c45070, 0x25afd373, 0x36ff2087, 0xc494a384,
	0x9a879fa0, 0x68ec1ca3, 0x7bbcef57, 0x89d76c54, 0x5d1d08bf, 0xaf768bbc, 0xbc267848, 0x4e4dfb4b,
	0x20bd8ede, 0xd2d60ddd, 0xc186fe29, 0x33ed7d2a, 0xe72719c1, 0x154c9ac2, 0x061c6936, 0xf477ea35,
	0xaa64d611, 0x580f5512, 0x4b5fa6e6, 0xb93425e5, 0x6dfe410e, 0x9f95c20d, 0x8cc531f9, 0x7eaeb2fa,
	0x30e349b1, 0xc288cab2, 0xd1d83946, 0x23b3ba45, 0xf779deae, 0x05125dad, 0x1642ae59, 0xe4292d5a,
	0xba3a117e, 0x4851927d, 0x5b016189, 0xa96ae28a, 0x7da08661, 0x8fcb0562, 0x9c9bf696, 0x6ef07595,
	0x417b1dbc, 0xb3109ebf, 0xa0406d4b, 0x522bee48, 0x86e18aa3, 0x748a09a0, 0x67dafa54, 0x95b17957,
	0xcba24573, 0x39c9c670, 0x2a993584, 0xd8f2b687, 0x0c38d26c, 0xfe53516f, 0xed03a29b, 0x1f682198,
	0x5125dad3, 0xa34e59d0, 0xb01eaa24, 0x42752927, 0x96bf4dcc, 0x64d4cecf, 0x77843d3b, 0x85efbe38,
	0xdbfc821c, 0x2997011f, 0x3ac7f2eb, 0xc8ac71e8, 0x1c661503, 0xee0d9600, 0xfd5d65f4, 0x0f36e6f7,
	0x61c69362, 0x93ad1061, 0x80fde395, 0x72966096, 0xa65c047d, 0x5437877e, 0x4767748a, 0xb50cf789,
	0xeb1fcbad, 0x197448ae, 0x0a24bb5a, 0xf84f3859, 0x2c855cb2, 0xdeeedfb1, 0xcdbe2c45, 0x3fd5af46,
	0x7198540d, 0x83f3d70e, 0x90a324fa, 0x62c8a7f9, 0xb602c312, 0x44694011, 0x5739b3e5, 0xa55230e6,
	0xfb410cc2, 0x092a8fc1, 0x1a7a7c35, 0xe811ff36, 0x3cdb9bdd, 0xceb018de, 0xdde0eb2a, 0x2f8b6829,
	0x82f63b78, 0x709db87b, 0x63cd4b8f, 0x91a6c88c, 0x456cac67, 0xb7072f64, 0xa457dc90, 0x563c5f93,
	0x082f63b7, 0xfa44e0b4, 0xe9141340, 0x1b7f9043, 0xcfb5f4a8, 0x3dde77ab, 0x2e8e845f, 0xdce5075c,
	0x92a8fc17, 0x60c37f14, 0x73938ce0, 0x81f80fe3, 0x55326b08, 0xa759e80b, 0xb4091bff, 0x466298fc,
	0x1871a4d8, 0xea1a27db, 0xf94ad42f, 0x0b21572c, 0xdfeb33c7, 0x2d80b0c4, 0x3ed04330, 0xccbbc033,
	0xa24bb5a6, 0x502036a5, 0x4370c551, 0xb11b4652, 0x65d122b9, 0x97baa1ba, 0x84ea524e, 0x7681d14d,
	0x2892ed69, 0xdaf96e6a, 0xc9a99d9e, 0x3bc21e9d, 0xef087a76, 0x1d63f975, 0x0e330a81, 0xfc588982,
	0xb21572c9, 0x407ef1ca, 0x532e023e, 0xa145813d, 0x758fe5d6, 0x87e466d5, 0x94b49521, 0x66df1622,
	0x38cc2a06, 0xcaa7a905, 0xd9f75af1, 0x2b9cd9f2, 0xff56bd19, 0x0d3d3e1a, 0x1e6dcdee, 0xec064eed,
	0xc38d26c4, 0x31e6a5c7, 0x22b65633, 0xd0ddd530, 0x0417b1db, 0xf67c32d8, 0xe52cc12c, 0x1747422f,
	0x49547e0b, 0xbb3ffd08, 0xa86f0efc, 0x5a048dff, 0x8ecee914, 0x7ca56a17, 0x6ff599e3, 0x9d9e1ae0,
	0xd3d3e1ab, 0x21b862a8, 0x32e8915c, 0xc083125f, 0x144976b4, 0xe622f5b7, 0xf5720643, 0x07198540,
	0x590ab964, 0xab613a67, 0xb831c993, 0x4a5a4a90, 0x9e902e7b, 0x6cfbad78, 0x7fab5e8c, 0x8dc0dd8f,
	0xe330a81a, 0x115b2b19, 0x020bd8ed, 0xf0605bee, 0x24aa3f05, 0xd6c1bc06, 0xc5914ff2, 0x37faccf1,
	0x69e9f0d5, 0x9b8273d6, 0x88d28022, 0x7ab90321, 0xae7367ca, 0x5c18e4c9, 0x4f48173d, 0xbd23943e,
	0xf36e6f75, 0x0105ec76, 0x12551f82, 0xe03e9c81, 0x34f4f86a, 0xc69f7b69, 0xd5cf889d, 0x27a40b9e,
	0x79b737ba, 0x8bdcb4b9, 0x988c474d, 0x6ae7c44e, 0xbe2da0a5, 0x4c4623a6, 0x5f16d052, 0xad7d5351
]

#size-byte
crcm32exInit = 0xFFFFFFFF
def CalCrcm32Ex(datalist, size, initvalue):

    if 1 == size % 2:

        return 0
    else:

        crc = initvalue

        for index in range(0, size):
            crc = crcm32TableEx[(crc ^ (datalist[index] & 0xFF)) & 0xFF] ^ (crc >> 8)

    return crc

crc32TableEx =[\
	0x00000000, 0x77073096, 0xEE0E612C, 0x990951BA, 0x076DC419, 0x706AF48F, 0xE963A535, 0x9E6495A3,
	0x0EDB8832, 0x79DCB8A4, 0xE0D5E91E, 0x97D2D988, 0x09B64C2B, 0x7EB17CBD, 0xE7B82D07, 0x90BF1D91,
	0x1DB71064, 0x6AB020F2, 0xF3B97148, 0x84BE41DE, 0x1ADAD47D, 0x6DDDE4EB, 0xF4D4B551, 0x83D385C7,
	0x136C9856, 0x646BA8C0, 0xFD62F97A, 0x8A65C9EC, 0x14015C4F, 0x63066CD9, 0xFA0F3D63, 0x8D080DF5,
	0x3B6E20C8, 0x4C69105E, 0xD56041E4, 0xA2677172, 0x3C03E4D1, 0x4B04D447, 0xD20D85FD, 0xA50AB56B,
	0x35B5A8FA, 0x42B2986C, 0xDBBBC9D6, 0xACBCF940, 0x32D86CE3, 0x45DF5C75, 0xDCD60DCF, 0xABD13D59,
	0x26D930AC, 0x51DE003A, 0xC8D75180, 0xBFD06116, 0x21B4F4B5, 0x56B3C423, 0xCFBA9599, 0xB8BDA50F,
	0x2802B89E, 0x5F058808, 0xC60CD9B2, 0xB10BE924, 0x2F6F7C87, 0x58684C11, 0xC1611DAB, 0xB6662D3D,
	0x76DC4190, 0x01DB7106, 0x98D220BC, 0xEFD5102A, 0x71B18589, 0x06B6B51F, 0x9FBFE4A5, 0xE8B8D433,
	0x7807C9A2, 0x0F00F934, 0x9609A88E, 0xE10E9818, 0x7F6A0DBB, 0x086D3D2D, 0x91646C97, 0xE6635C01,
	0x6B6B51F4, 0x1C6C6162, 0x856530D8, 0xF262004E, 0x6C0695ED, 0x1B01A57B, 0x8208F4C1, 0xF50FC457,
	0x65B0D9C6, 0x12B7E950, 0x8BBEB8EA, 0xFCB9887C, 0x62DD1DDF, 0x15DA2D49, 0x8CD37CF3, 0xFBD44C65,
	0x4DB26158, 0x3AB551CE, 0xA3BC0074, 0xD4BB30E2, 0x4ADFA541, 0x3DD895D7, 0xA4D1C46D, 0xD3D6F4FB,
	0x4369E96A, 0x346ED9FC, 0xAD678846, 0xDA60B8D0, 0x44042D73, 0x33031DE5, 0xAA0A4C5F, 0xDD0D7CC9,
	0x5005713C, 0x270241AA, 0xBE0B1010, 0xC90C2086, 0x5768B525, 0x206F85B3, 0xB966D409, 0xCE61E49F,
	0x5EDEF90E, 0x29D9C998, 0xB0D09822, 0xC7D7A8B4, 0x59B33D17, 0x2EB40D81, 0xB7BD5C3B, 0xC0BA6CAD,
	0xEDB88320, 0x9ABFB3B6, 0x03B6E20C, 0x74B1D29A, 0xEAD54739, 0x9DD277AF, 0x04DB2615, 0x73DC1683,
	0xE3630B12, 0x94643B84, 0x0D6D6A3E, 0x7A6A5AA8, 0xE40ECF0B, 0x9309FF9D, 0x0A00AE27, 0x7D079EB1,
	0xF00F9344, 0x8708A3D2, 0x1E01F268, 0x6906C2FE, 0xF762575D, 0x806567CB, 0x196C3671, 0x6E6B06E7,
	0xFED41B76, 0x89D32BE0, 0x10DA7A5A, 0x67DD4ACC, 0xF9B9DF6F, 0x8EBEEFF9, 0x17B7BE43, 0x60B08ED5,
	0xD6D6A3E8, 0xA1D1937E, 0x38D8C2C4, 0x4FDFF252, 0xD1BB67F1, 0xA6BC5767, 0x3FB506DD, 0x48B2364B,
	0xD80D2BDA, 0xAF0A1B4C, 0x36034AF6, 0x41047A60, 0xDF60EFC3, 0xA867DF55, 0x316E8EEF, 0x4669BE79,
	0xCB61B38C, 0xBC66831A, 0x256FD2A0, 0x5268E236, 0xCC0C7795, 0xBB0B4703, 0x220216B9, 0x5505262F,
	0xC5BA3BBE, 0xB2BD0B28, 0x2BB45A92, 0x5CB36A04, 0xC2D7FFA7, 0xB5D0CF31, 0x2CD99E8B, 0x5BDEAE1D,
	0x9B64C2B0, 0xEC63F226, 0x756AA39C, 0x026D930A, 0x9C0906A9, 0xEB0E363F, 0x72076785, 0x05005713,
	0x95BF4A82, 0xE2B87A14, 0x7BB12BAE, 0x0CB61B38, 0x92D28E9B, 0xE5D5BE0D, 0x7CDCEFB7, 0x0BDBDF21,
	0x86D3D2D4, 0xF1D4E242, 0x68DDB3F8, 0x1FDA836E, 0x81BE16CD, 0xF6B9265B, 0x6FB077E1, 0x18B74777,
	0x88085AE6, 0xFF0F6A70, 0x66063BCA, 0x11010B5C, 0x8F659EFF, 0xF862AE69, 0x616BFFD3, 0x166CCF45,
	0xA00AE278, 0xD70DD2EE, 0x4E048354, 0x3903B3C2, 0xA7672661, 0xD06016F7, 0x4969474D, 0x3E6E77DB,
	0xAED16A4A, 0xD9D65ADC, 0x40DF0B66, 0x37D83BF0, 0xA9BCAE53, 0xDEBB9EC5, 0x47B2CF7F, 0x30B5FFE9,
	0xBDBDF21C, 0xCABAC28A, 0x53B39330, 0x24B4A3A6, 0xBAD03605, 0xCDD70693, 0x54DE5729, 0x23D967BF,
	0xB3667A2E, 0xC4614AB8, 0x5D681B02, 0x2A6F2B94, 0xB40BBE37, 0xC30C8EA1, 0x5A05DF1B, 0x2D02EF8D
]

#size-byte
crc32exInit = 0xc3c33c3c
def CalCrc32Ex(datalist, size, initvalue):

    if 1 == size % 2:

        return 0
    else:

        crc = initvalue

        for index in range(0, size):
            crc = crc32TableEx[(crc ^ (datalist[index] & 0xFF)) & 0xFF] ^ (crc >> 8)

    return crc

def IsSubString(SubStrList, Str):
    flag = True
    for substr in SubStrList:
        if not (substr in Str):
            flag = False
    return flag


def GetFileList(FindPath, FlagStr):
    FileList = []
    FileNames = os.listdir(FindPath)
    for fn in FileNames:
        if (IsSubString(FlagStr, fn)):
            fullfilename = os.path.join(FindPath, fn)
            FileList.append(fullfilename)
    return FileList
#--------------------------------------------------------class--------------------------------------------------------#

class IniParser:
    #--------------------------property--------------------------#
    __FileList = 0
    __IniPar = configparser.ConfigParser()
    __TestInfo = []
    __CurTest = []
    __TestIndex = 0
    __CommIndex = 0
    __TestFinish = False
    __Mode = 0

    #--------------------------init--------------------------#

    # def __init__(self):

    #--------------------------interface--------------------------#

    def ParseIni(self):
        Result = self.__GetIniFile()

        if 0 != Result:
            return Result

        self.__IniPar.read(self.__FileList)

        Result = self.__CheckIniFile()

        if 0 != Result:
            return Result

        self.__TestInfo = self.__IniPar["TestInfo"]
        self.__CurTest = self.__IniPar["Test1"]
        self.__TestIndex = 1
        self.__CommIndex = int(self.__CurTest["StrIndex"])

        Result = self.__DealMode()

        if 0 != Result:
            return Result

        return Result

    def AddCommIndex(self):
        self.__CommIndex += 1
        self.__CheckAndChange()

    def IsTestFinish(self):
        return self.__TestFinish

    def GetCurTest(self):
        return self.__CurTest

    def GetTestInfo(self):
        return self.__TestInfo

    def GetCommIndex(self):
        return self.__CommIndex

    def GetMode(self):
        return self.__Mode

    #--------------------------method--------------------------#

    def __GetIniFile(self):
        # FindPath = os.getcwd()
        FindPath = "D:/TestComm"

        FlagStr = ['ini']
        self.__FileList = GetFileList(FindPath, FlagStr)

        zcanpro.write_log(FindPath)

        if 0 == len(self.__FileList):
            zcanpro.write_log("No ini file, Plesse add one ini file")
            return -1
        elif 1 < len(self.__FileList):
            zcanpro.write_log("More than one ini files, Please leave one ini file!")
            return -1
        else:
            zcanpro.write_log(str(self.__FileList))
            return 0

    def __CheckIniFile(self):

        try:
            TestInfo = self.__IniPar["TestInfo"]
        except:
            zcanpro.write_log("No TestInfo .ini file!")
            return -1

        try:
            TestInfo["BoardType"]
            TestInfo["SysAorB"]
            TestInfo["MorS"]
            TestInfo["UseCha"]
            TestNum = TestInfo["TestNum"]
            zcanpro.write_log("TestNum :"+TestNum)
        except:
            zcanpro.write_log("Less Parm in TestInfo!")
            return -1

        for index in range(int(TestNum)):
            Test = "Test" + str(index + 1)

            try:
                TestIndex = self.__IniPar[Test]
                zcanpro.write_log(Test)

                try:
                    TestIndex["StrIndex"]
                    TestIndex["EndIndex"]
                    TestIndex["TimeStampOffset"]
                    TestIndex["CrcM"]
                    TestIndex["Crc"]
                    TestIndex["SendTimes"]
                    TestIndex["UseCha"]
                    TestIndex["CandID"]

                except:
                    zcanpro.write_log("Less Parm in "+Test)
                    return -1

            except:
                zcanpro.write_log("No" + Test)
                return -1
        zcanpro.write_log("Check OK")

        return 0

    def __CheckAndChange(self):

        if self.__CommIndex > int(self.__CurTest["EndIndex"]):
            if self.__TestIndex < int(self.__TestInfo["TestNum"]):
                self.__TestIndex += 1
                self.__CurTest = self.__IniPar["Test"+str(self.__TestIndex)]
                self.__CommIndex = int(self.__CurTest["StrIndex"])
            else:
                self.__TestFinish = True

    def __DealMode(self):

        boardType = self.__TestInfo["BoardType"]

        if type('str') == type(boardType):
            if "MS" == boardType:
                self.__Mode = "MS_Mode"
            else:
                self.__Mode = "EXE_Mode"
        else:
            zcanpro.write_log("More than one board in BoardType!")
            return -1

        zcanpro.write_log("Mode:" + self.__Mode)
        return 0

#--------------------------------------------------------class--------------------------------------------------------#
class BoardParser:
    #--------------------------property--------------------------#
    BoardType = "NULL"
    IDType = {"MS":0, "DI":1, "DO":2, "FI":3, "AI":4, "REV":6}
    IDAorB = {"A":0, "B":1}
    IDPkgType = {"State":1, "Ver":2, "Req":3, "Req2":6}

    headStru = {"Time":0, "Index":0, "Len":64, "Type":0, "MorS":0}
    channel = {"Cha1": [0], "Cha2": [1], "ChaAll": [0,1]}
    headData = []
    valueData = []
    crcCrcM = []
    zCanPro = 0

    #--------------------------init--------------------------#

    # def __init__(self):
    #--------------------------interface--------------------------#
    def is_belong(self, BoardType):
        if self.BoardType == BoardType:
            return True

    def make_id(self, idType, idAorB, idPkgType):
        #3-1-7
        id = self.IDType[idType]
        id <<= 1
        id += self.IDAorB[idAorB]
        id <<= 7
        id += self.IDPkgType[idPkgType]

        return id

    def run(self, iniPar, recvData):
        pass

    def frame(self, pkgType, timeStamp, index, crcm, crc):
        pass

    def send(self, id, useCha):

        data = self.headData + self.valueData + self.crcCrcM
        for chaIndex in self.channel[useCha]:
            self.zCanPro.send(chaIndex, id, data)


    #first update headStru from TestX
    def frame_headdata(self):
        timeByte = 8
        indexByte = 2
        lenByte = 2
        typeByte = 1
        mOrsByte = 1

        #{"Time":0, "Index":0, "Len":64, "Type":0, "MorS":0}

        self.headData.clear()

        for index in range(timeByte):
            self.headData.append((self.headStru["Time"] >> (8 * index)) & 0xFF)

        for index in range(2):
            self.headData.append((self.headStru["Index"] >> (8 * index)) & 0xFF)

        for index in range(lenByte):
            self.headData.append((self.headStru["Len"] >> (8 * index)) & 0xFF)

        for index in range(typeByte):
            self.headData.append((self.headStru["Type"] >> (8 * index)) & 0xFF)

        for index in range(mOrsByte):
            self.headData.append((self.headStru["MorS"] >> (8 * index)) & 0xFF)

    def frame_valuedata(self, pkgType):
        pass

    def frame_crc_crcm(self, crcmIn, crcIn):
        self.crcCrcM.clear()

        #crcm
        if "NULL" == crcmIn:
            crcm = CalCrcm32Ex(self.valueData, len(self.valueData), crcm32exInit)
        else:
            crcm = int(crcmIn)

        crcbyte = 4
        for index in range(crcbyte):
            self.crcCrcM.append((crcm >> (8 * index)) & 0xFF)

        #crc
        if "NULL" == crcIn:
            crc = CalCrc32Ex(self.headData, len(self.headData), crc32exInit)
            crc = CalCrc32Ex(self.valueData, len(self.valueData), crc)
            crc = CalCrc32Ex(self.crcCrcM, len(self.crcCrcM), crc)
        else:
            crc = int(crcIn)

        crcbyte = 4
        for index in range(crcbyte):
            self.crcCrcM.append((crc >> (8 * index)) & 0xFF)

    def make_board_type(self, strType ,strAB):
        board = self.IDType[strType] * 2 + self.IDAorB[strAB]

        return board

    #--------------------------method--------------------------#


#--------------------------------------------------------class--------------------------------------------------------#
class MSParser(BoardParser):
    #--------------------------property--------------------------#
    __sendIndex = 1
    __stage = {"State":1, "Ver":6, "Req":11}
    __pkgType = {"State": 1, "Ver": 2, "Req": 3}
    __mOrS = {"AA":0xAA, "AB":0xAB, "BA":0xBA, "BB":0xBB}
    __mOrSValue = 0
    __timeStamp = 0
    __boardType = 0
    __sysRunCmd = 0
    __sleepTime = 0
    __stateValueData = [0x00,0x00,0x11,0x11,0x00,0x00,0x00,0x00,0xfc,0xff,
                        0xff,0x07,0xff,0xff,0xff,0xff,0xb2,0x0c,0xb2,0x0c,
                        0x00,0x00,0x00,0x00,0x11,0x11,0x00,0x00,0x00,0x00,
                        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                        0x00,0x00]
    __verValueData = [0x00,0x00,0x01,0x00,0x07,0x20,0x20,0x00,0x56,0x34,
                      0x12,0x00,0x00,0x00,0x00,0x00,0x70,0x20,0x01,0x10,
                      0x71,0x20,0x01,0x10,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00,0x19,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00]
    __reqValueData = [0x14,0x00,0x00,0x03,0x08,0x00,0x55,0x55,0x55,0x55,
                      0x55,0x55,0x55,0x55,0x55,0x55,0x55,0x55,0x55,0x55,
                      0x55,0x55,0x69,0x05,0xeb,0x13,0x00,0x00,0x00,0x00,
                      0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00]

    #--------------------------init--------------------------#

    def __init__(self, zCanPro):
        self.BoardType = "MS"
        self.zCanPro = zCanPro

    #--------------------------interface--------------------------#
    def run(self, iniPar, recvData):

        testInfo = iniPar.GetTestInfo()
        self.__mOrSValue = self.__mOrS[testInfo["MorS"]]
        self.__boardType = self.make_board_type(testInfo["BoardType"], testInfo["SysAorB"])

        if False == iniPar.IsTestFinish():

            curTest = iniPar.GetCurTest()

            if "NULL" == curTest["TimeStampOffset"]:
                self.__timeStamp += int(self.__sleepTime * 1000)
            else:
                self.__timeStamp += int(curTest["TimeStampOffset"])

            if self.__sendIndex >= self.__stage["Req"]:
                if 1 == self.__sendIndex % 2:
                    self.__sleepTime = 0.022
                    strType = "Req"
                else:
                    self.__sleepTime = 0.078
                    strType = "State"

                self.__sysRunCmd = 0x3333

            elif self.__sendIndex >= self.__stage["Ver"]:
                if self.__sendIndex == (self.__stage["Req"] - 1):
                    self.__sleepTime = 0.078
                else:
                    self.__sleepTime = 0.1
                strType = "Ver"
                self.__sysRunCmd = 0x1111

            else:
                self.__sleepTime = 0.1
                strType = "State"
                self.__sysRunCmd = 0x1111

            if "NULL" == curTest["CandID"]:
                id = self.make_id(self.BoardType, testInfo["SysAorB"], strType)
            else:
                id = int(curTest["CandID"])

            #get current test
            pkgType = self.__pkgType[strType]
            timeStamp = self.__timeStamp
            index = iniPar.GetCommIndex()
            crcm = curTest["CrcM"]
            crc = curTest["Crc"]
            sendTimes = int(curTest["SendTimes"])
            useCha = curTest["UseCha"]

            self.frame(pkgType, timeStamp, index, crcm, crc)

            for sendIndex in range(sendTimes):
                self.send(id, useCha)

            self.__sendIndex += 1
            iniPar.AddCommIndex()

            time.sleep(self.__sleepTime)

    def frame(self, pkgType, timeStamp, index, crcm, crc):

        # headStru = {"Time":0, "Index":0, "Len":64, "Type":0, "MorS":0}
        self.headStru["Time"] = timeStamp
        self.headStru["Index"] = index
        self.headStru["Len"] = 64
        self.headStru["Type"] = pkgType
        self.headStru["MorS"] = self.__mOrSValue

        self.frame_headdata()
        self.frame_valuedata(pkgType)
        self.frame_crc_crcm(crcm, crc)


    def frame_valuedata(self, pkgType):

        self.valueData.clear()
        if self.__pkgType["State"] == pkgType:
            self.valueData.extend(self.__stateValueData)
            self.valueData[0] = self.__boardType & 0xff
            self.valueData[20] = self.__sysRunCmd & 0xff
            self.valueData[21] = (self.__sysRunCmd >> 8) & 0xff

        elif self.__pkgType["Ver"] == pkgType:
            self.valueData.extend(self.__verValueData)
            self.valueData[0] = self.__boardType & 0xff

        elif self.__pkgType["Req"] == pkgType:
            self.valueData.extend(self.__reqValueData)
            self.valueData[0] = self.__boardType & 0xff

    #--------------------------method--------------------------#

#--------------------------------------------------------class--------------------------------------------------------#
class ExeParser(BoardParser):
    #--------------------------property--------------------------#
    replyNum = 0
    __sendIndex = 1
    pkgType = {"State": 1, "Ver": 2, "Req": 3, "Req2":6}
    __timeStamp = 0
    __boardType = 0
    __sysRunCmd = 0

    stateValueData = []
    verValueData = []
    reqValueData = []
    req2ValueData = []

    #--------------------------init--------------------------#

    def __init__(self, zCanPro):
        self.BoardType = "NULL"
        self.zCanPro = zCanPro

    #--------------------------interface--------------------------#
    def run(self, iniPar, recvData):

        testInfo = iniPar.GetTestInfo()

        self.__boardType = self.make_board_type(testInfo["BoardType"], testInfo["SysAorB"])

        if False == iniPar.IsTestFinish() \
                and len(recvData["type"]) == len(recvData["timeStamp"]) \
                and 0 < len(recvData["type"]):

            for recvIndex in range(len(recvData["type"])):
                if 1 == self.replyNum or \
                        (2 == self.replyNum and "Req" != recvData["type"][recvIndex]):

                    curTest = iniPar.GetCurTest()

                    strType = recvData["type"][recvIndex]
                    self.__sysRunCmd = 0x3333

                    if "NULL" == curTest["CandID"]:
                        id = self.make_id(self.BoardType, testInfo["SysAorB"], strType)
                    else:
                        id = int(curTest["CandID"])

                    if "NULL" != curTest["TimeStampOffset"]:
                        self.__timeStamp += int(curTest["TimeStampOffset"])
                    else:
                        self.__timeStamp = recvData["timeStamp"][recvIndex]

                    #get current test
                    pkgType = self.pkgType[strType]
                    timeStamp = self.__timeStamp
                    index = iniPar.GetCommIndex()
                    crcm = curTest["CrcM"]
                    crc = curTest["Crc"]
                    sendTimes = int(curTest["SendTimes"])
                    useCha = curTest["UseCha"]

                    self.frame(pkgType, timeStamp, index, crcm, crc)

                    for sendIndex in range(sendTimes):
                        self.send(id, useCha)

                    self.__sendIndex += 1
                    iniPar.AddCommIndex()

                elif 2 == self.replyNum and "Req" == recvData["type"][recvIndex]:
                    #pkg 1
                    curTest = iniPar.GetCurTest()

                    strType = recvData["type"][recvIndex]
                    self.__sysRunCmd = 0x3333

                    if "NULL" == curTest["CandID"]:
                        id = self.make_id(self.BoardType, testInfo["SysAorB"], strType)
                    else:
                        id = int(curTest["CandID"])

                    self.__timeStamp = recvData["timeStamp"][recvIndex]
                    if "NULL" != curTest["TimeStampOffset"]:
                        self.__timeStamp += int(curTest["TimeStampOffset"])

                    # get current test
                    pkgType = self.pkgType[strType]
                    timeStamp = self.__timeStamp
                    index = iniPar.GetCommIndex()
                    crcm = curTest["CrcM"]
                    crc = curTest["Crc"]
                    sendTimes = int(curTest["SendTimes"])
                    useCha = curTest["UseCha"]

                    self.frame(pkgType, timeStamp, index, crcm, crc)

                    for sendIndex in range(sendTimes):
                        self.send(id, useCha)

                    self.__sendIndex += 1
                    iniPar.AddCommIndex()

                    # pkg 2
                    curTest = iniPar.GetCurTest()

                    strType = "Req2"
                    self.__sysRunCmd = 0x3333

                    if "NULL" == curTest["CandID"]:
                        id = self.make_id(self.BoardType, testInfo["SysAorB"], strType)
                    else:
                        id = int(curTest["CandID"])

                    self.__timeStamp = recvData["timeStamp"][recvIndex]
                    if "NULL" != curTest["TimeStampOffset"]:
                        self.__timeStamp += int(curTest["TimeStampOffset"])

                    # get current test
                    pkgType = self.pkgType[strType]
                    timeStamp = self.__timeStamp
                    index = iniPar.GetCommIndex()
                    crcm = curTest["CrcM"]
                    crc = curTest["Crc"]
                    sendTimes = int(curTest["SendTimes"])
                    useCha = curTest["UseCha"]

                    self.frame(pkgType, timeStamp, index, crcm, crc)

                    for sendIndex in range(sendTimes):
                        self.send(id, useCha)

                    self.__sendIndex += 1
                    iniPar.AddCommIndex()



    def frame(self, pkgType, timeStamp, index, crcm, crc):

        # headStru = {"Time":0, "Index":0, "Len":64, "Type":0, "MorS":0}
        self.headStru["Time"] = timeStamp
        self.headStru["Index"] = index
        self.headStru["Len"] = 64
        self.headStru["Type"] = pkgType
        self.headStru["MorS"] = 0

        self.frame_headdata()
        self.frame_valuedata(pkgType)
        self.frame_crc_crcm(crcm, crc)


    def frame_valuedata(self, pkgType):

        self.valueData.clear()
        if self.pkgType["State"] == pkgType:
            self.valueData.extend(self.stateValueData)
            self.valueData[0] = self.__boardType & 0xff
            self.valueData[20] = self.__sysRunCmd & 0xff
            self.valueData[21] = (self.__sysRunCmd >> 8) & 0xff

        elif self.pkgType["Ver"] == pkgType:
            self.valueData.extend(self.verValueData)
            self.valueData[0] = self.__boardType & 0xff

        elif self.pkgType["Req"] == pkgType:
            self.valueData.extend(self.reqValueData)

        elif self.pkgType["Req2"] == pkgType:
            self.valueData.extend(self.req2ValueData)

    #--------------------------method--------------------------#

#--------------------------------------------------------class--------------------------------------------------------#
class DIParser(ExeParser):
    #--------------------------property--------------------------#

    __stateValueData = [0x03,0x00,0x33,0x33,0x00,0x00,0x00,0x00,0x7f,0xff,
                        0xff,0x00,0xff,0xff,0xff,0xff,0xc1,0x0c,0x50,0x0c,
                        0x7c,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                        0x00,0x00]
    __verValueData = [0x03,0x00,0x01,0x00,0x78,0x56,0x34,0x12,0x44,0x44,
                      0x33,0x33,0x22,0x22,0x11,0x11,0x74,0x20,0x01,0x10,
                      0x75,0x20,0x01,0x10,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00,0x4f,0x03,0x7c,0x01,0x00,0x00,0x00,0x00,
                      0x00,0x00]
    __reqValueData = [0x28,0x00,0x00,0xb2,0x10,0x00,0x55,0x55,0x55,0x55,
                      0x55,0x55,0x55,0x55,0x55,0x55,0x55,0x55,0x55,0x55,
                      0x55,0x55,0x55,0x55,0x55,0x55,0x55,0x55,0x55,0x55,
                      0x55,0x55,0x55,0x55,0x55,0x55,0x55,0x55,0x86,0xad,
                      0x10,0x46]

    #--------------------------init--------------------------#

    def __init__(self, zCanPro):
        self.BoardType = "DI"
        self.replyNum = 1
        self.zCanPro = zCanPro

        self.stateValueData.clear()
        self.stateValueData.extend(self.__stateValueData)
        self.verValueData.clear()
        self.verValueData.extend(self.__verValueData)
        self.reqValueData.clear()
        self.reqValueData.extend(self.__reqValueData)

    #--------------------------interface--------------------------#

    # --------------------------method--------------------------#

#--------------------------------------------------------class--------------------------------------------------------#
class DOParser(ExeParser):
    #--------------------------property--------------------------#

    __stateValueData = [0x04,0x00,0x33,0x33,0x00,0x00,0x00,0x00,0x7f,0xff,
                        0x03,0x00,0xff,0xff,0xff,0xff,0xcd,0x0d,0x29,0x0b,
                        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                        0x00,0x00]
    __verValueData = [0x04,0x00,0x01,0x00,0x78,0x56,0x34,0x12,0x44,0x44,
                      0x33,0x33,0x22,0x22,0x11,0x11,0x76,0x20,0x01,0x10,
                      0x77,0x20,0x01,0x10,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00,0x33,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00]
    __reqValueData = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00]

    #--------------------------init--------------------------#

    def __init__(self, zCanPro):
        self.BoardType = "DO"
        self.replyNum = 1
        self.zCanPro = zCanPro

        self.stateValueData.clear()
        self.stateValueData.extend(self.__stateValueData)
        self.verValueData.clear()
        self.verValueData.extend(self.__verValueData)
        self.reqValueData.clear()
        self.reqValueData.extend(self.__reqValueData)

        self.IDPkgType["Req"] = 5
        self.pkgType["Req"] = 5

    #--------------------------interface--------------------------#

    # --------------------------method--------------------------#

#--------------------------------------------------------class--------------------------------------------------------#
class FIParser(ExeParser):
    #--------------------------property--------------------------#

    __stateValueData = [0x06,0x00,0x33,0x33,0x00,0x00,0x00,0x00,0x7f,0x03,
                        0x00,0x00,0xff,0xff,0xff,0xff,0x02,0x0d,0xb6,0x0c,
                        0x13,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                        0x00,0x00]
    __verValueData = [0x06,0x00,0x01,0x00,0x78,0x56,0x34,0x12,0x44,0x44,
                      0x33,0x33,0x22,0x22,0x11,0x11,0x78,0x20,0x01,0x10,
                      0x79,0x20,0x01,0x10,0x60,0x20,0x00,0x00,0x60,0x20,
                      0x00,0x00,0x93,0x1d,0x13,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00]
    __reqValueData = [0x24,0x00,0x01,0xa4,0x0e,0x00,0xff,0xff,0xff,0xff,
                      0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xff,0xff,
                      0xff,0xff,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                      0xff,0xff,0x00,0x00,0x66,0xa7,0x6b,0x27,0x00,0x00,
                      0x00,0x00]
    __req2ValueData = [0x24,0x00,0x02,0xa4,0x0e,0x00,0xff,0xff,0xff,0xff,
                       0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xff,0xff,
                       0xff,0xff,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                       0xff,0xff,0x00,0x00,0x42,0x76,0xdc,0x4c,0x00,0x00,
                       0x00,0x00]

    #--------------------------init--------------------------#

    def __init__(self, zCanPro):
        self.BoardType = "FI"
        self.replyNum = 2
        self.zCanPro = zCanPro

        self.stateValueData.clear()
        self.stateValueData.extend(self.__stateValueData)
        self.verValueData.clear()
        self.verValueData.extend(self.__verValueData)
        self.reqValueData.clear()
        self.reqValueData.extend(self.__reqValueData)
        self.req2ValueData.clear()
        self.req2ValueData.extend(self.__req2ValueData)

    #--------------------------interface--------------------------#

    # --------------------------method--------------------------#

#--------------------------------------------------------class--------------------------------------------------------#
class AIParser(ExeParser):
    #--------------------------property--------------------------#

    __stateValueData = [0x08,0x00,0x33,0x33,0x00,0x00,0x00,0x00,0x7f,0x00,
                        0x00,0x00,0xff,0xff,0xff,0xff,0x00,0x00,0x00,0x00,
                        0x61,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                        0x00,0x00]
    __verValueData = [0x08,0x00,0x01,0x00,0x78,0x56,0x34,0x12,0x44,0x44,
                      0x33,0x33,0x22,0x22,0x11,0x11,0x73,0x20,0x00,0x00,
                      0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00,0x64,0x03,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00]
    __reqValueData = [0x1c,0x00,0x00,0xa6,0x0a,0x00,0x55,0x55,0x00,0x00,
                      0x55,0x55,0x00,0x00,0x55,0x55,0x00,0x00,0x55,0x55,
                      0x00,0x00,0x55,0x55,0x00,0x00,0xac,0xaa,0x79,0xbd,
                      0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                      0x00,0x00]
    __req2ValueData = [0x18,0x00,0x00,0xa5,0x02,0x00,0x00,0x00,0x00,0x00,
                       0x23,0x4e,0xf4,0xcc,0x00,0xa1,0x02,0x00,0x00,0x00,
                       0x00,0x00,0x87,0xdd,0xa2,0xa1,0x00,0x00,0x00,0x00,
                       0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                       0x00,0x00]

    #--------------------------init--------------------------#

    def __init__(self, zCanPro):
        self.BoardType = "AI"
        self.replyNum = 2
        self.zCanPro = zCanPro

        self.stateValueData.clear()
        self.stateValueData.extend(self.__stateValueData)
        self.verValueData.clear()
        self.verValueData.extend(self.__verValueData)
        self.reqValueData.clear()
        self.reqValueData.extend(self.__reqValueData)
        self.req2ValueData.clear()
        self.req2ValueData.extend(self.__req2ValueData)

    #--------------------------interface--------------------------#

    # --------------------------method--------------------------#


#--------------------------------------------------------canpro--------------------------------------------------------#
stopTask = False

class ZCanPro:
    #--------------------------property--------------------------#
    buses = 0
    __msAID = (0x1, 0x2, 0x3)
    __msBID = (0x81, 0x82, 0x83)
    __pkgType = ("State", "Ver", "Req")
    #--------------------------init--------------------------#

    def __init__(self):
        self.buses = zcanpro.get_buses()
        zcanpro.write_log("Get buses: " + str(self.buses))

    def get_buses(self):
        return self.buses

    def send(self, chaIndex, id, data):
        frms = [{
            "can_id": id,              # 帧ID
            "is_canfd": 1,              # 是否为CANFD数据, 0-CAN, 1-CANFD
            "canfd_brs": 1,             # CANFD加速, 0-不加速, 1-加速
            "data": data,    # 数据
            "timestamp_us": 666666      # 时间戳, 微妙
        }]

        result = zcanpro.transmit(self.buses[chaIndex]["busID"], frms)
        if not result:
            zcanpro.write_log("chaIndex-" + str(chaIndex))
            zcanpro.write_log("id-" + str(id))
            zcanpro.write_log("data len-" + str(len(data)))
            zcanpro.write_log("Transmit error!")

    def recv_deal_data(self):

        recvData = {"type":[], "timeStamp":[]}

        #only use channel 0
        result, frms = zcanpro.receive(self.buses[0]["busID"])
        if not result:
            zcanpro.write_log("Receive error!")
        elif len(frms) > 0:
            for dataIndex in range(len(frms)):
                for idIndex in range(len(self.__msAID)):

                    if self.__msAID[idIndex] == frms[dataIndex]["can_id"] or \
                            self.__msBID[idIndex] == frms[dataIndex]["can_id"]:

                        recvData["type"].append(self.__pkgType[idIndex])

                        timeStamp = 0
                        for timeIndex in range(8):
                            timeStamp <<= 8
                            timeStamp += frms[dataIndex]["data"][7 - timeIndex]

                        recvData["timeStamp"].append(timeStamp)
                        break

        return  recvData

    #--------------------------interface--------------------------#


def z_notify(type, obj):
    zcanpro.write_log("Notify " + str(type) + " " + str(obj))
    if type == "stop":
        zcanpro.write_log("Stop...")
        global stopTask
        stopTask = True


def z_main():
    zcanpro.write_log("Comm Test Start!")
    global stopTask

#parse ini file
    iniPar = IniParser()

    Result = iniPar.ParseIni()

    if 0 != Result:
        return Result

#get can bus info
    zCanPro = ZCanPro()

#check ini and canbus match
    if 2 != len(zCanPro.get_buses()):
        zcanpro.write_log("Dont have 2 can channels!")
        return

#init Board
    boardType = iniPar.GetTestInfo()["BoardType"]
    if "MS" == boardType:
        useBDPar = MSParser(zCanPro)
    elif "DI" == boardType:
        useBDPar = DIParser(zCanPro)
    elif "DO" == boardType:
        useBDPar = DOParser(zCanPro)
    elif "FI" == boardType:
        useBDPar = FIParser(zCanPro)
    elif "AI" == boardType:
        useBDPar = AIParser(zCanPro)
    else:
        zcanpro.write_log("Cant Find Board Parser")
        return

    zcanpro.write_log("Find Board Parser:" + boardType)

#Run

    mode = iniPar.GetMode()

    while not stopTask:

        # deal recv
        if "EXE_Mode" == mode:
            recvData = zCanPro.recv_deal_data()
            if 0 < len(recvData):
                time.sleep(0.001)
        else:
            recvData = "NULL"

        useBDPar.run(iniPar, recvData)

        if True == iniPar.IsTestFinish():
            zcanpro.write_log("Comm Test Finish!")
            break


