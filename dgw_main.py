#-*- coding: utf8 -*-
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
import fileinput
import sys, os
import socket
import time
import datetime
import psycopg2
import psycopg2.extras
import struct
import hashlib
from urllib import parse
sys.path.append('C:\\Python34\\mysite\\bobo')
sys.path.append('C:\\Python34\\mysite\\broker')
import ProdConvert
import db_test
global seq
global comm02_contract_data
seq = 1700
comm02_contract_data = []
cosy_all = "F039000"
curr_response_global = {'TWD':'NTD','CN$':'RMB','US$':'USD'}
decode_glogal = "cp950"
ErrorMSG_inipath = "C:\\Python34\\mysite\\bobo\\ErrorMSG.ini"
logtxtpath = "C:\\Python34\\mysite\\DGW\\dgw_main_log.txt"
proxy_response_xmlpath = "C:\\Python34\\proxy_response.xml"
proxy_response_log_xmlpath = "C:\\Python34\\proxy_response_xml\\"#
success_code_list = ['0000','0001','0002','0003','0004','0006','R000','R001','R002','R006','R009','STAR']#無錯誤回應代碼
DB_str = "host=127.0.0.1 port=5432 user=postgres dbname=NewFirst password=0000"#order_server 共用資料庫路徑
HK_DB_str = "host=127.0.0.1 port=5432 user=postgres dbname=NewFirst password=0000"#港股資料庫路徑
ZF_socket = ('192.168.210.75',9112)#中菲socket (IP,port)
ZF_test_socket = ('203.69.245.142',9112)#中菲測試機socket (IP,port)
ZF_socket_trade = ('192.168.150.126',9112)#中菲正式機(交易)socket (IP,port)
ZF_socket_accounting = ('192.168.150.127',9112)#中菲正式機(帳務)socket (IP,port)
#==== BASIC FUNCTION ====
def read_ErrorMSG():#open ErrorMSG.ini
    f = open(ErrorMSG_inipath,"r")
    og_lines = f.readlines()
    lines = [i.split('\n',1)[0] for i in og_lines]
    #print(lines)
    f.close
    return lines
def key_exist_in_object(key_,object):
    if key_ in object:
        return object[key_]
    else:
        return ''
def write_log_txt(object):
    #logList = read_log_txt()
    f = open(logtxtpath,"a",encoding="utf8")
    f.write("\n[" + str(datetime.datetime.now()) + "]" + str(object))
    f.close()
def write_log_txt_without_datetime(object):
    f = open(logtxtpath,"a",encoding="utf8")
    f.write("\n" + str(object))
    f.close()
def sha_sign(before_sign_str_):
    shavalue = hashlib.sha256()
    #write_log_txt('====sha_sign===='+str(before_sign_str_).strip())
    data = str(before_sign_str_).strip()
    shavalue.update(data.encode('utf8'))
    return shavalue.hexdigest()
def hex_ord(string_):
    result = ''
    for r in string_:
        result = result+hex(ord(r))
    return result
def r_ord(string_):
    result = ''
    for r in string_:
        result = result+ord(r)
    return result
def ErrorMSG_to_dict():#Example ErrorMSG_to_dict()['TSC0017']  '後檯:有留倉部位!不可下新單', Example2 ErrorMSG_to_dict()['1010005'] '委託條件錯誤'
    dict = {}
    lines = read_ErrorMSG()
    for item in lines:
        dict.update({item.strip().split('==')[0]:item.strip().split('==')[1]})
    return dict
#==== DB operation function ====
def insert_DB_proxy_pxbs(daily_sn, tdate, sett, comm, symb, agls, lino, sels, orsh, orpr, orpt, ortr, orcn, orse):
    #換回中菲的原始值
    bs_ = get_bs(agls)
    orpt_ = get_orpt(orpt)
    orcn_ = get_orcn(orcn)
    ortr_ = get_ortr(ortr)
    #lino_ = get_lino(lino,sels)#20160520 這個暫時不必了

    try:
        DB_conn_ = psycopg2.connect(DB_str)
        DB_conn_.autocommit = True
        DB_conn_.set_client_encoding('BIG5')
        DB_cursor_ = DB_conn_.cursor()
        #insert DB parameter : 0 0 tdate sett comm symb losh lino orsh orpr orpt ortr orcn orse
        selectStr = "select public.sf_proxy_pxbs_insert('"+daily_sn+"','"+daily_sn+"','"+tdate+"','"+cosy_all+"','"+sett+"','"+comm+"','"+symb+"','"+bs_+"','"+lino+"','"+orsh+"','"+orpr+"','"+orpt_+"','"+ortr_+"','"+orcn_+"','"+orse+"')"
        #write_log_txt("["+str(datetime.datetime.now())+"]==== insert_DB_proxy_pxbs ===="+selectStr)
        DB_cursor_.execute(selectStr)
        DB_conn_.close()
    except:
        write_log_txt("==== insert_DB_proxy_pxbs ERROR ===="+str(sys.exc_info()[0]))
        write_log_txt(selectStr)

def insert_DB_proxy_pxbs_without_query(tdate, sett, comm, symb, agls, lino, sels, orsh, orpr, orpt, ortr, orcn, orse):
    #換回中菲的原始值
    bs_ = get_bs(agls)
    orpt_ = get_orpt(orpt)
    orcn_ = get_orcn(orcn)
    ortr_ = get_ortr(ortr)
    #lino_ = get_lino(lino,sels)#20160520 這個暫時不必了

    try:
        DB_conn_ = psycopg2.connect(DB_str)
        DB_conn_.autocommit = True
        DB_conn_.set_client_encoding('BIG5')
        DB_cursor_ = DB_conn_.cursor()
        #insert DB parameter : sett comm symb losh lino orsh orpr orpt ortr orcn orse
        selectStr = "select public.sf_proxy_pxbs_insert_without_query('"+tdate+"','"+cosy_all+"','"+sett+"','"+comm+"','"+symb+"','"+bs_+"','"+lino+"','"+orsh+"','"+orpr+"','"+orpt_+"','"+ortr_+"','"+orcn_+"','"+orse+"')"
        DB_cursor_.execute(selectStr)
        DB_conn_.close()
    except:
        write_log_txt("==== insert_DB_proxy_pxbs_without_query ERROR ====")

def query_today_DB_proxy_pxbs():
    try:
        DB_conn_ = psycopg2.connect(DB_str)
        DB_conn_.autocommit = True
        DB_conn_.set_client_encoding('BIG5')
        DB_cursor_ = DB_conn_.cursor()
        #select DB parameter : sett comm symb losh lino orsh orpr orpt ortr orcn orse
        selectStr = "select * from public.tb_proxy_pxbs_symb_record where tdate >= '"+str(datetime.datetime.now())[0:10].replace('-','')+"'"
        DB_cursor_.execute(selectStr)
        results = DB_cursor_.fetchall()
        DB_conn_.close()
        return results
    except:
        write_log_txt("==== query_today_DB_proxy_pxbs ERROR ====")

def HK_DB_select_connect(sqlcmd):#return list of tuple
    try:
        DB_conn_ = psycopg2.connect(HK_DB_str)
    except:
        #print "Can't connect to Working DB"
        sys.exit(0)
        
    DB_conn_.autocommit = True  
    DB_conn_.set_client_encoding('UTF8')
    DB_cursor_ = DB_conn_.cursor()
    #DB_cursor_.execute("insert into public.tb_broker_log(log_level,msg,error_msg) VALUES (\'DEBUG\',\'DB_select_connect\',\'"+sqlcmd.replace('\'','')+"\')")
    DB_cursor_.execute(sqlcmd)

    results = DB_cursor_.fetchall()
    DB_conn_.close()
    return results

def response_lock_unlock():
    if response_lock.locked():
        try:
            response_lock.release()#20160913 避免港股下單前,上次的異常lock未解
        except:
            write_log_txt(' response_lock release ERROR ='+str(sys.exc_info()))
            pass

def yyymmdd_mutual_yyyymmdd(date_str,Concatenation):#西元民國date互轉
    result = ""
    date_str = date_str.replace('/','').replace('-','')
    if len(date_str) == 7:
        result = str(int(date_str[:3])+1911)+Concatenation+date_str[3:5]+Concatenation+date_str[5:7]
    else:
        result = str(int(date_str[:4])-1911)+Concatenation+date_str[4:6]+Concatenation+date_str[6:8]
    return result
def bobo_main_socket(str_,mode_):
    global seq
    item_list = parse.unquote(parse.unquote(str_)).split('&')
    item_dic = {}
    for item in item_list:
        if len(item.split('='))==2:
            item_dic.update({item.split('=')[0]:item.split('=')[1]})
        elif len(item.split('='))==1:
            item_dic.update({item.split('=')[0]:item.split('=')[0]})
        else:
            item_dic.update({item.split('=')[0]:item[item.find('=')+1:]})

    if mode_ == '000':
        body = item_dic['idno'][:10]+'       '+'       '+'0'+'A'+item_dic['pass'].ljust(20,' ')+'192.168.210.75           '
        log_body = item_dic['idno'][:10]+'       '+'       '+'0'+'A'+'********************'+'192.168.210.75           '
    elif mode_ == '000_P':
        mode_ = '000'
        #b = ProdConvert.customer_data("","",item_dic['sett'],DB_str)#補足客戶資料的類別
        body = '          '+cosy_all+item_dic['sett']+'3'+'F'+item_dic['pwd'].ljust(20,' ')+'192.168.210.75           '
        log_body = '          '+cosy_all+item_dic['sett']+'3'+'F'+'********************'+'192.168.210.75           '
    #elif mode_ == '001':
        #b = ProdConvert.customer_data("","",item_dic['sett'],DB_str)#補足客戶資料的類別
        #body = b.id+cosy_all+item_dic['sett']
    elif mode_ == '002':
        if item_dic['cate'] in ['0',0]:#登入密碼
            body = '0'+item_dic['oldpass'].ljust(20, ' ')+item_dic['pass'].ljust(20, ' ')+item_dic['idno']+'       '+'       '+'192.168.210.75           '
        else:#出金密碼
            body = '3'+item_dic['oldpass'].ljust(20, ' ')+item_dic['pass'].ljust(20, ' ')+item_dic['idno']+'       '+'       '+'192.168.210.75           '
    elif mode_ == '004':#出入金銀行帳號查詢
        body = cosy_all+item_dic['sett']+'*'+'1'+'*  '
    elif mode_ == '100':
        #bs_ = get_bs(item_dic['losh'])#20160523 規則修改
        orpt_ = get_orpt(item_dic['orpt'])
        orcn_ = get_orcn(item_dic['orcn'])
        ortr_ = get_ortr(item_dic['ortr'])
        lino_ = item_dic['lino']#get_lino(item_dic['lino'],item_dic['sels'])
        #轉換商品代碼 20160318
        if lino_ == '1':#期貨單式
            bs_ = get_bs(item_dic['losh'])
            #a = ProdConvert.DazhouToZhongfei("1", DB_str, item_dic['symb'], item_dic['losh'], item_dic['exdt'], item_dic['stpr'], item_dic['capu'], item_dic['losh'], item_dic['seed'], item_dic['sesp'], item_dic['secp'], item_dic['sels'])
        elif lino_ == '4':#期貨複式
            #a = ProdConvert.DazhouToZhongfei("4", DB_str, item_dic['symb'], item_dic['losh'], item_dic['exdt'], item_dic['stpr'], item_dic['capu'], item_dic['losh'], item_dic['seed'], item_dic['sesp'], item_dic['secp'], item_dic['sels'])
            if ':' in item_dic['symb']:
                bs_ = get_bs(item_dic['losh'])
            else:
                bs_ = get_bs(item_dic['sels'])
        elif lino_ == '2':#選擇權單式
            bs_ = get_bs(item_dic['losh'])
            """
            if item_dic['symb'] in ['TXO','TFO','XIO','TX1','TX2','TX4','TX5']:
                stpr_ = str(int(item_dic['stpr'])/10).replace('.0','').rjust(5, '0')
            else:
                stpr_ = item_dic['stpr'].rjust(5, '0')
            a = ProdConvert.DazhouToZhongfei("0", DB_str, item_dic['symb'], item_dic['losh'], item_dic['exdt'], stpr_, item_dic['capu'], item_dic['losh'], item_dic['seed'], item_dic['sesp'], item_dic['secp'], item_dic['sels'])
            """
        elif lino_ == '3':#選擇權複式
            """
            if item_dic['symb'] in ['TXO','TFO','XIO','TX1','TX2','TX4','TX5']:
                stpr_ = str(int(item_dic['stpr'])/10).replace('.0','').rjust(5, '0')
                sesp_ = str(int(item_dic['sesp'])/10).replace('.0','').rjust(5, '0')
            else:
                stpr_ = item_dic['stpr'].rjust(5, '0')
                sesp_ = item_dic['sesp'].rjust(5, '0')
            a = ProdConvert.DazhouToZhongfei("3", DB_str, item_dic['symb'], item_dic['losh'], item_dic['exdt'], stpr_, item_dic['capu'], item_dic['losh'], item_dic['seed'], sesp_, item_dic['secp'], item_dic['sels'])
            """
            if ':' in item_dic['symb']:
                bs_ = get_bs(item_dic['losh'])
            else:
                bs_ = get_bs(item_dic['sels'])
        #b = ProdConvert.customer_data("","",item_dic['sett'],DB_str)#補足客戶資料的類別
        #20160824 增加對簽章欄位的判斷方便測試(若無簽章值則使用不簽章模式) 
        #20171227 ajax呼叫一定要驗簽 測試完成後關閉無簽章資訊的分歧
        #20180103 ajax呼叫直接帶相關參數(中菲)不需另外轉
        if item_dic['tasignature'].strip() == '':
            #body = cosy_all+item_dic['sett']+item_dic['symb'].ljust(20, ' ')+item_dic['bs']+item_dic['orpt']+item_dic['orpr'].rjust(11, ' ')+item_dic['orsh'].rjust(4, ' ')+item_dic['orcn']+item_dic['ortr']+item_dic['lino']+'192.168.210.75           '+'a'+'N              '#+b.id.ljust(15,' ')+item_dic['tasignature']
            body = cosy_all+item_dic['sett']+item_dic['stockid'].ljust(20, ' ')+bs_+orpt_+item_dic['orpr'].rjust(11, ' ')+item_dic['orsh'].rjust(4, ' ')+orcn_+ortr_+lino_+'192.168.210.75           '+'a'+'N              '#+b.id.ljust(15,' ')+item_dic['tasignature']#
        else:
            #body = cosy_all+item_dic['sett']+item_dic['symb'].ljust(20, ' ')+item_dic['bs']+item_dic['orpt']+item_dic['orpr'].rjust(11, ' ')+item_dic['orsh'].rjust(4, ' ')+item_dic['orcn']+item_dic['ortr']+item_dic['lino']+'192.168.210.75           '+'a'+item_dic['idno'].ljust(15,' ')+item_dic['tasignature'].replace('%3D',chr(0x3d)).replace('%2F',chr(0x2f)).replace('%2B',chr(0x2b)).replace('\r\n',chr(0x0d)+chr(0x0a))#+'N              '
            body = cosy_all+item_dic['sett']+item_dic['stockid'].ljust(20, ' ')+bs_+orpt_+item_dic['orpr'].rjust(11, ' ')+item_dic['orsh'].rjust(4, ' ')+orcn_+ortr_+lino_+'192.168.210.75           '+'a'+item_dic['idno'].ljust(15,' ')+item_dic['tasignature'].replace('%3D',chr(0x3d)).replace('%2F',chr(0x2f)).replace('%2B',chr(0x2b)).replace('\r\n',chr(0x0d)+chr(0x0a))#+'N              '
    elif mode_ == '101':
        """
        if real_select_results[0][0][:1] == 'A':
            order = '0'#預約單 0
        else:
            order = '1'#盤中單 1
        """
        if item_dic['tasignature'].strip() == '':
            body = item_dic['orst']+item_dic['execType']+cosy_all+item_dic['comm']+item_dic['sett']+item_dic['symb'].ljust(20, ' ')+item_dic['losh']+item_dic['orpt']+item_dic['orpr'].rjust(11, ' ')+item_dic['orsh'].rjust(4, ' ')+item_dic['orcn']+item_dic['ortr']+item_dic['lino']+'192.168.210.75           '+'a'+item_dic['InputSource2']+item_dic['orse']+yyymmdd_mutual_yyyymmdd(item_dic['date'],'')+'N              '
        else:
            body = item_dic['orst']+item_dic['execType']+cosy_all+item_dic['comm']+item_dic['sett']+item_dic['symb'].ljust(20, ' ')+item_dic['losh']+item_dic['orpt']+item_dic['orpr'].rjust(11, ' ')+item_dic['orsh'].rjust(4, ' ')+item_dic['orcn']+item_dic['ortr']+item_dic['lino']+'192.168.210.75           '+'a'+item_dic['InputSource2']+item_dic['orse']+yyymmdd_mutual_yyyymmdd(item_dic['date'],'')+item_dic['idno'].ljust(15,' ')+item_dic['tasignature'].replace('%3D','=').replace('%2F','/').replace('%2B','+').replace('\r\n',chr(0x0d)+chr(0x0a))#+'N              '
        """
        對照real_select_results[0][?]
        select comm, symb, bs, lino, orsh, orpr, orpt, ortr, orcn, orse, tdate 
         [?]    0    1     2   3     4     5     6     7     8     9     10
        
        原始body字串組成:
        body = '1'+get_type(item_dic['type'])+cosy_all+item_dic['comm']+item_dic['sett']+symb_.ljust(20, ' ')+bs_+orpt_+item_dic['orpr'].rjust(11, ' ')+item_dic['orsh'].rjust(4, ' ')+orcn_+ortr_+lino_+'192.168.210.75           '+' '+item['orse'][:3]+item['orse'][3:]+str(datetime.datetime.now())[0:10].replace('-','')+'N              '#+b.id.ljust(15,' ')+item_dic['tasignature']
        
        DCN GATEWAY 20171215
        原始body字串組成:
        body = ' '+item_dic['type']+cosy_all+item_dic['comm']+item_dic['sett']+item_dic['symb'].ljust(20, ' ')+item_dic['orpt']+item_dic['orpr'].rjust(11, ' ')+item_dic['orsh'].rjust(4, ' ')+item_dic['orcn']+item_dic['ortr']+item_dic['lino']+'192.168.210.75           '+'a'+item['orse'][:3]+item['orse'][3:]+item['date']+'N              '

        """
    elif mode_ == '102':#102 103 主動委託回報 主動成交回報
        body = '00000000'
    elif mode_ == '200':
        body = 'I'+item_dic['cosy']+item_dic['sett']+'   '+'      '+'3'+'       '+'     0'+'              0'+' '+' '+'       '+'     0'+'              0'+' '+' '
    elif mode_ == '201':
        body = 'I'+item_dic['cosy']+item_dic['sett']+'3'#1:單式  2:複式  3:全部
    elif mode_ == '202':
        body = 'I'+cosy_all+item_dic['sett']
    elif mode_ == '203':
        body = cosy_all+item_dic['sett']
    elif mode_ == '204':
        body = item_dic['cosy']+item_dic['sett']+yyymmdd_mutual_yyyymmdd(item_dic['date'],'')+yyymmdd_mutual_yyyymmdd(item_dic['date1'],'')
    elif mode_ == '207':
        if len(key_exist_in_object('Currency',item_dic))>0:
            body = cosy_all+item_dic['sett']+'   '+'      '+item_dic['Currency']#查詢子帳客戶所有組別資料傳'***',(組別三碼)
        else:
            body = cosy_all+item_dic['sett']+'   '+'      '+'ALL'#查詢子帳客戶所有組別資料傳'***',(組別三碼)
    elif mode_ == '208':
        if str(datetime.datetime.now())[0:4]+str(datetime.datetime.now())[5:7]+str(datetime.datetime.now())[8:10]>yyymmdd_mutual_yyyymmdd(item_dic['date1'],''):
            return []
        body = cosy_all+item_dic['sett']
    elif mode_ == '209':
        if str(datetime.datetime.now())[0:4]+str(datetime.datetime.now())[5:7]+str(datetime.datetime.now())[8:10]>yyymmdd_mutual_yyyymmdd(item_dic['date1'],''):
            return []
        body = cosy_all+item_dic['sett']
    elif mode_ == '211':
        body = cosy_all+item_dic['sett']+yyymmdd_mutual_yyyymmdd(item_dic['date'],'')+yyymmdd_mutual_yyyymmdd(item_dic['date1'],'')
    elif mode_ == '212':
        body = cosy_all+item_dic['sett']+yyymmdd_mutual_yyyymmdd(item_dic['date'],'')+yyymmdd_mutual_yyyymmdd(item_dic['date1'],'')
    elif mode_ == '201_HK':
        return HK_DB_select_connect("select * from dfh.tb_cntl where branch_no = '"+item_dic['comp']+"' and cust_id = '"+item_dic['sett'].rjust(7,'0')[0:6]+"' and cust_cofirm = '"+item_dic['sett'].rjust(7,'0')[6:]+"'")
    elif mode_ == '208_HK':
        #20160825 只查每張comm(term+desq)最新狀態的委託回報
        #sqlcmd_ = "select * from dfh.sf_request_pxbs_inside_plus('', '', '', '', '', 0, 9999) INNER JOIN (select max(order_sn) as sn from dfh.cs_pxbs \
        #            where bhno = '"+item_dic['comp']+"' and cseq = '"+item_dic['sett'].rjust(7,'0')[0:6]+"' \
        #            and ckno = '"+item_dic['sett'].rjust(7,'0')[6:]+"' and tdate = '"+str(datetime.datetime.now())[0:4]+str(datetime.datetime.now())[5:7]+str(datetime.datetime.now())[8:10]+"'\
        #            GROUP BY term,desq) a ON order_sn = a.sn"

        sqlcmd_ = "select * from dfh.sf_request_pxbs_inside_plus('', '', '', '', '', 0, 9999) \
                    where bhno = '"+item_dic['comp']+"' and cseq = '"+item_dic['sett'].rjust(7,'0')[0:6]+"' \
                    and ckno = '"+item_dic['sett'].rjust(7,'0')[6:]+"' and tdate = '"+str(datetime.datetime.now())[0:4]+str(datetime.datetime.now())[5:7]+str(datetime.datetime.now())[8:10]+"'"
        return HK_DB_select_connect(sqlcmd_)
    elif mode_ == '209_HK':
        return HK_DB_select_connect("select * from dfh.cs_pxmh where deal_sn < 1000 and bhno = '"+item_dic['comp']+"' and cseq = '"+item_dic['sett'].rjust(7,'0')[0:6]+"' and ckno = '"+item_dic['sett'].rjust(7,'0')[6:]+"' and tdate = '"+str(datetime.datetime.now())[0:4]+str(datetime.datetime.now())[5:7]+str(datetime.datetime.now())[8:10]+"'")
    elif mode_ == '306':
        #20160711 出金銀行帳號 comm=8220174&symb=174533261983
        curr_dict = {'CNY':'CN$','USD':'US$','TWD':'TWD','RMB':'CN$','NTD':'TWD','CN$':'CN$','US$':'US$'}
        Curr_ = key_exist_in_object(item_dic['Currency'],curr_dict)
        if item_dic['ExecType'] == '2':#出金申請刪除
            if item_dic['tasignature'].strip() == '':
                body = '000'+item_dic['sett']+Curr_+get_orpr(item_dic['Amount']).rjust(15, ' ')+key_exist_in_object('BankID',item_dic).ljust(7, ' ')+key_exist_in_object('BankAccoount',item_dic).ljust(20, ' ')+yyymmdd_mutual_yyyymmdd(item_dic['TradeDate'],'')+'2'+'Y'+'192.168.210.75           '+'   '+'      '+item_dic['ApplySource']+item_dic['ApplyNo']+'N              '
            else:
                body = '000'+item_dic['sett']+Curr_+get_orpr(item_dic['Amount']).rjust(15, ' ')+key_exist_in_object('BankID',item_dic).ljust(7, ' ')+key_exist_in_object('BankAccoount',item_dic).ljust(20, ' ')+yyymmdd_mutual_yyyymmdd(item_dic['TradeDate'],'')+'2'+'Y'+'192.168.210.75           '+'   '+'      '+item_dic['ApplySource']+item_dic['ApplyNo']+item_dic['idno'].ljust(15,' ')+item_dic['tasignature'].replace('%3D','=').replace('%2F','/').replace('%2B','+').replace('\r\n',chr(0x0d)+chr(0x0a))
            #body = '000'+item_dic['sett']+item_dic['mark'].split('_')[1]+get_orpr(item_dic['orpr']).rjust(15, ' ')+key_exist_in_object('comm',item_dic).ljust(7, ' ')+key_exist_in_object('symb',item_dic).ljust(20, ' ')+date_temp_str+'2'+'Y'+'192.168.210.75           '+'   '+'      '+item_dic['orse'][0:3]+item_dic['orse'][3:9]+'N              '
        else:#出金申請
            if item_dic['tasignature'].strip() == '':
                body = '000'+item_dic['sett']+Curr_+get_orpr(item_dic['Amount']).rjust(15, ' ')+key_exist_in_object('BankID',item_dic).ljust(7, ' ')+key_exist_in_object('BankAccoount',item_dic).ljust(20, ' ')+yyymmdd_mutual_yyyymmdd(item_dic['TradeDate'],'')+'1'+'Y'+'192.168.210.75           '+'   '+'      '+'   '+'      '+'N              '
            else:
                body = '000'+item_dic['sett']+Curr_+get_orpr(item_dic['Amount']).rjust(15, ' ')+key_exist_in_object('BankID',item_dic).ljust(7, ' ')+key_exist_in_object('BankAccoount',item_dic).ljust(20, ' ')+yyymmdd_mutual_yyyymmdd(item_dic['TradeDate'],'')+'1'+'Y'+'192.168.210.75           '+'   '+'      '+'   '+'      '+item_dic['idno'].ljust(15,' ')+item_dic['tasignature'].replace('%3D','=').replace('%2F','/').replace('%2B','+').replace('\r\n',chr(0x0d)+chr(0x0a))
            #body = '000'+item_dic['sett']+item_dic['mark'].split('_')[1]+get_orpr(item_dic['orpr']).rjust(15, ' ')+key_exist_in_object('comm',item_dic).ljust(7, ' ')+key_exist_in_object('symb',item_dic).ljust(20, ' ')+date_temp_str+'1'+'Y'+'192.168.210.75           '+'   '+'      '+'   '+'      '+'N              '
    elif mode_ == '307':
        body = 'I'+cosy_all+item_dic['sett']
    elif mode_ == '309':
        body = item_dic['execType']+cosy_all+item_dic['sett']+yyymmdd_mutual_yyyymmdd(item_dic['date'],'')+'192.168.210.75           '+item_dic['idno'].ljust(15,' ')+item_dic['tasignature'].replace('%3D',chr(0x3d)).replace('%2F',chr(0x2f)).replace('%2B',chr(0x2b)).replace('\r\n',chr(0x0d)+chr(0x0a))
    elif mode_ == '310':
        body = 'I'+cosy_all+item_dic['sett']+yyymmdd_mutual_yyyymmdd(item_dic['date'],'')+yyymmdd_mutual_yyyymmdd(item_dic['date1'],'')
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(ZF_socket)
        """
        if mode_ in ['100','101']:#交易
            sock.connect(ZF_socket_trade)
        else:#帳務
            sock.connect(ZF_socket_accounting)
        """
    except:
        write_log_txt("====ERROR==== sock.connect('192.168.210.75',9112)")

    length = len(body)
    length1 = int(length / 256)
    length2 = length % 256
    
    now_time_str = str(datetime.datetime.now())[11:13]+str(datetime.datetime.now())[14:16]+str(datetime.datetime.now())[17:19]+str(datetime.datetime.now())[20:23]
    
    head_start = chr(0x11)
    head = now_time_str+str(seq).rjust(10, '0')+mode_+'000'+'       '+'               '
    seq = seq + 1
    #body_length1 = chr(int(hex(length1),16))
    #body_length2 = chr(int(hex(length2),16))
    end = chr(0x0a)
    if mode_ != '000':#20170807 log裡面password不顯示明碼
        log_body = body	
    write_log_txt(' send body='+(head_start+head+str(struct.pack('B',length1)+struct.pack('B',length2))+log_body+end))
    sock.send((head_start+head).encode('ascii')+struct.pack('B',length1)+struct.pack('B',length2)+(body+end).encode('ascii'))
    #sock.send((head_start+hex_ord(head)+length_1+length_2+hex_ord(body)+end).replace('0x','').encode('ascii'))

    #========================== 從中菲接收 start ==========================
    if mode_ not in ['000','000_P','001','002','100','101','306','309']:
        recv_size = 0
        if mode_ == '004':
            recv_size = 142#91+1+50
            total_ceil = 85
            total_floor = 78
            now_ceil = 92
            now_floor = 85
        elif mode_ == '200':#庫存(當日未平倉明細)
            recv_size = 544#+50+1
            total_ceil = 67
            total_floor = 60
            now_ceil = 74
            now_floor = 67
        elif mode_ == '201':#庫存
            recv_size = 437#+50+1
            total_ceil = 67
            total_floor = 60
            now_ceil = 74
            now_floor = 67
        elif mode_ == '203':
            recv_size = 394#343+50+1
            total_ceil = 81
            total_floor = 74
            now_ceil = 88
            now_floor = 81
        elif mode_ == '204':#庫存歷史
            recv_size = 385#334+50+1
            total_ceil = 57
            total_floor = 50
            now_ceil = 64
            now_floor = 57
        elif mode_ == '207':#權益數查詢
            recv_size = 719#668+1+50
            total_ceil = 90
            total_floor = 83
            now_ceil = 97
            now_floor = 90
        elif mode_ == '208':#委託回補
            recv_size = 232#181+1+50
            total_ceil = 57
            total_floor = 50
            now_ceil = 64
            now_floor = 57
        elif mode_ == '209':#成交回補
            recv_size = 211#159+1+50
            total_ceil = 57
            total_floor = 50
            now_ceil = 64
            now_floor = 57
        elif mode_ == '211':#歷史委託回補
            recv_size = 232#181+1+50
            total_ceil = 57
            total_floor = 50
            now_ceil = 64
            now_floor = 57
        elif mode_ == '212':#歷史成交回補
            recv_size = 211#159+1+50
            total_ceil = 57
            total_floor = 50
            now_ceil = 64
            now_floor = 57
        elif mode_ == '306':#出金申請
            recv_size = 269#218+1+50
            total_ceil = 91
            total_floor = 84
            now_ceil = 98
            now_floor = 91
        elif mode_ == '307':
            recv_size = 225#174+1+50
            total_ceil = 67
            total_floor = 60
            now_ceil = 74
            now_floor = 67
        elif mode_ == '310':
            recv_size = 218#167+1+50
            total_ceil = 57
            total_floor = 50
            now_ceil = 64
            now_floor = 57
        list_recv_data = []
        try:
            while True:
                cut_data = ""
                single_data = sock.recv(recv_size)
                write_log_txt_without_datetime(single_data)
                if int.from_bytes(single_data[49:50],byteorder='little') == 0 and len(single_data) == 51:#查無資料就不再查了
                    if single_data[26:33].decode(decode_glogal).strip() == '9990004':
                        list_recv_data.append(single_data)#放一組用來做"後台結帳中"訊息
                    write_log_txt( mode_+" data empty BREAK ")
                    break
                elif len(single_data) != recv_size:#從接收端下手
                    cut_data = sock.recv(recv_size - len(single_data))
                    write_log_txt(mode_+" socket data re TRY ")
                    single_data = single_data+cut_data
                    #write_log_txt(single_data)
                    list_recv_data.append(single_data)
                else:
                    #write_log_txt("===="+mode_+" NORMAL ====")
                    list_recv_data.append(single_data)

                if int(single_data[now_floor:now_ceil].decode(decode_glogal).strip()) == int(single_data[total_floor:total_ceil].decode(decode_glogal).strip()):
                    write_log_txt(mode_+" data recv finish BREAK size = "+str(len(list_recv_data)))
                    break
        except:
            write_log_txt(mode_+" data recv from ZF ERROR ")
        return list_recv_data
    else:#000,000_P,001,002,100,101,306
        recv_size = 512
        data = sock.recv(recv_size)#20171129 萬一一次不夠用 (用結尾判斷)
        if len(data) > 0:
            while True:
                try:
                    if data[len(data)-1:len(data)] == b'\n':
                        write_log_txt(mode_+" future recv data =")
                        write_log_txt_without_datetime(data)
                        break
                    else:
                        data = data+sock.recv(recv_size)
                except:
                    write_log_txt(debug+" future recv data except=")
                    write_log_txt_without_datetime(data)
                    break
        else:
            data = b'\x110957220980000001700777AP17770000               \x00\x00'
        return data
    sock.close()
    #========================== 從中菲接收 end ==========================
#region ==== MAPPING FUNC start ====
# ==== 100 ====
def get_bs(item_):#買賣別
    bs_ = ""
    if item_ == '1':
        bs_ = 'B'
    elif item_ == '2':
        bs_ = 'S'
    elif item_ == 'B':
        bs_ = '1'
    elif item_ == 'S':
        bs_ = '2'
    return bs_
def get_orpt(item_):#價格別(ZF 委託方式)
    orpt_ = ""
    orpt_dict = {'10':'M','M':'10','0':'L','L':'0','15':'P','P':'15'}
    orpt_ = key_exist_in_object(item_,orpt_dict)
    #if orpt_ == "":
        #orpt_ = "10"#預設值10
    return orpt_
def get_orcn(item_):#委託條件
    orcn_ = ""
    if item_ == '10':
        orcn_ = 'F'
    elif item_ == '20':
        orcn_ = 'I'
    elif item_ == '0':
        orcn_ = 'R'
    return orcn_
def get_ortr(item_):#沖銷別(開平倉碼)
    ortr_ = ""
    if item_ == '0':
        ortr_ = '0'
    elif item_ == '1':
        ortr_ = '1'
    elif item_ == '4':
        ortr_ = '2'
    else:
        ortr_ = ' '
    return ortr_
def get_lino(item_lino,item_sels):#市場別
    lino_ = ""
    if item_lino == '1' and item_sels in ['0','undefined']:
        lino_ = '1'
    elif item_lino == '2' and item_sels in ['0','undefined']:
        lino_ = '2'
    elif item_lino == '2' and item_sels != '0':
        lino_ = '3'
    elif item_lino == '1' and item_sels != '0':
        lino_ = '4'
    return lino_
# ==== 101 ====
def get_type(item_):
    type_ = ""
    if item_ == '30':
        type_ = '4'
    elif item_ == '20':
        type_ = '5'
    elif item_ == '15':
        type_ = 'M'
    elif item_ == '0':
        type_ = '0'
    return type_
def get_orpr(item_):
    if len(str(item_).split('.')) > 1:
        return str(float(item_))
    else:
        return str(item_)
# ==== 201 ====
def get_capu(item_):
    capu_dict = {'C':'1','P':'2','1':'C','2':'P','':'','F':'1'}
    return capu_dict[str(item_)]
# ==== 207 ====
def float_Positive_Negative(item_,Pos_result,Neg_result):
    result = ""
    if float(item_)>0:
        result = Pos_result
    else:
        result = Neg_result
    return result

#response orst組成
def make_orst(ZF_1,ZF_code):
    result = "90"#委託傳送交易所後未回報   暫時用在執行有錯誤
    if ZF_1 == '0':#委託單狀態
        if ZF_code == 'R000':#ZF 預約中
             result = '0'#預約單
        elif ZF_code == 'R001':#ZF 預約單減量
             result = '20'#改量
        elif ZF_code == 'R002':#ZF 預約單刪單成功
             result = '30'#委託取消
        elif ZF_code == 'R006':#ZF 預約單改價成功
             result = '15'#改價
        elif ZF_code == 'R009':#ZF 委託已送出
             result = '8'#
        else:
            result = '0'#預約單
    else:#ZF 委託單狀態 1  (盤中單)
        #用code來判斷
        if ZF_code == '0000':#ZF 委託成功
             result = '10'#委託成功
        if ZF_code == '0001':#ZF 減量成功
             result = '20'#改量
        if ZF_code == '0002':#ZF 刪單成功
             result = '30'#委託取消
        if ZF_code == '0003':#ZF 部分成交
             result = '10'#委託成功
        if ZF_code == '0004':#ZF 完全成交
             result = '50'#完全成交
        if ZF_code == '0006':#ZF 改價成功
             result = '15'#改價
    return result
#endregion ==== MAPPING FUNC end ====
def db_select_000(bhno_,cuna_,sett_,id_,FS_,temp_idno):
    try:
        DB_conn_ = psycopg2.connect(DB_str)
        DB_conn_.autocommit = True
        DB_conn_.set_client_encoding('BIG5')
        DB_cursor_ = DB_conn_.cursor()
        insertStr = ""
        if FS_ == 'F':
            selectStr = "select * from public.tb_customer where bhno = '"+bhno_+"' and cseq = '"+sett_+"' and account_mode ='2' and id ='"+id_+"'"
            DB_cursor_.execute(selectStr)
            results = DB_cursor_.fetchall()
            if len(results) == 0:
                insertStr = insertStr+"insert into public.tb_customer (bhno, department, cseq, name, id, status, cuser, account_mode, comp) \
    values ('"+bhno_+"','','"+sett_+"','"+cuna_+"','"+id_+"','1','proxy_default','2','15000');"
        else:
            selectStr = "select * from public.tb_customer where bhno = '"+bhno_+"' and cseq = '"+sett_.rjust(7,'0')+"' and account_mode ='1' and id ='"+id_+"'"
            DB_cursor_.execute(selectStr)
            results = DB_cursor_.fetchall()
            #write_log_txt("["+str(datetime.datetime.now())+"] "+str(results))
            if len(results) == 0:
                insertStr = insertStr+"insert into public.tb_customer (bhno, department, cseq, name, id, status, cuser, account_mode, comp) \
    values ('"+bhno_+"','','"+sett_.rjust(7,'0')+"','"+cuna_+"','"+id_+"','1','proxy_default','1','"+bhno_+"');"
            selectStr = "select * from public.tb_customer where bhno = '"+bhno_+"' and cseq = '"+sett_.rjust(7,'0')+"' and account_mode ='4' and id ='"+id_+"'"
            DB_cursor_.execute(selectStr)
            results = DB_cursor_.fetchall()
            if len(results) == 0:
                insertStr = insertStr+"insert into public.tb_customer (bhno, department, cseq, name, id, status, cuser, account_mode, comp) \
    values ('"+bhno_+"','','"+sett_.rjust(7,'0')+"','"+cuna_+"','"+id_+"','1','proxy_default','4','"+bhno_+"');"
        if len(insertStr)>0:
            DB_cursor_.execute(insertStr)
            #write_log_txt("["+str(datetime.datetime.now())+"] "+insertStr)
        DB_cursor_.close()
    except:
        write_log_txt(" db_select_000"+str(sys.exc_info()))
def db_select_branch():
    try:
        DB_conn_ = psycopg2.connect(DB_str)
        DB_conn_.autocommit = True
        DB_conn_.set_client_encoding('BIG5')
        DB_cursor_ = DB_conn_.cursor()
        selectStr = "select bhno,bhname,ap_id,comp from public.tb_branch"
        DB_cursor_.execute(selectStr)
        results = DB_cursor_.fetchall()
        DB_cursor_.close()
    except:
        write_log_txt(" db_select_branch"+str(sys.exc_info()))
    return results
def tran_future_000(data,temp_idno):
    re_dic = {}
    re_list = []
    if int.from_bytes(data[48:50],byteorder='little')>0:
        cut_count = int(data[50:53].decode(decode_glogal))
        for r in range(cut_count):
            re_list.append(data[53+50*r:103+50*r])
            if len(re_list) > 0:
                futures_account_list = []
                stock_account_list = []
                for item in re_list:
                    re_dic1 = {}#SBCMACUS
                    re_dic1.update({'sett':''})
                    #re_dic1.update({'comp':'6460'})
                    #re_dic1.update({'cosy':'6460'})
                    #re_dic1.update({'cona':'板橋大昌證券'})
                    #re_dic1.update({'ctno':'----------------------876543210'})
                    re_dic2 = {}#OBCMACUS
                    re_dic2.update({'sett':''})
                    re_dic2.update({'comp':'15000'})
                    #re_dic2.update({'cosy':cosy_all})
                    #re_dic2.update({'cona':'中菲期貨'})
                    #re_dic2.update({'ctno':'---------------------987654--10'})
                    if item[37:38].decode(decode_glogal) == 'I':#交易盤別,I=可交易國內盤
                        if item[0:1].decode(decode_glogal) == 'F':
                            re_dic2.update({'cosy':item[1:8].decode(decode_glogal).strip()})
                            #re_dic2.update({'cona':NameMapping[item[1:8].decode(decode_glogal).strip()]})
                            re_dic2.update({'cona':item[15:37].decode(decode_glogal).strip()})
                            re_dic2.update({'sett':item[8:15].decode(decode_glogal).strip()})
                            futures_account_list.append(re_dic2)
                        else:# item[0:1].decode(decode_glogal) == 'S'
                            re_dic1.update({'comp':item[1:8].decode(decode_glogal).strip()})
                            re_dic1.update({'cosy':item[1:8].decode(decode_glogal).strip()})
                            #re_dic1.update({'cona':NameMapping[item[1:8].decode(decode_glogal).strip()]})
                            re_dic1.update({'cona':item[15:37].decode(decode_glogal).strip()})
                            re_dic1.update({'sett':item[8:15].decode(decode_glogal).strip().rjust(7,'0')})
                            stock_account_list.append(re_dic1)
                    elif item[37:38].decode(decode_glogal) == 'O':#交易盤別,O=可交易國外盤
                        if item[0:1].decode(decode_glogal) == 'F':
                            re_dic2.update({'cosy':item[1:8].decode(decode_glogal).strip()})
                            #re_dic2.update({'cona':NameMapping[item[1:8].decode(decode_glogal).strip()]})
                            re_dic2.update({'cona':item[15:37].decode(decode_glogal).strip()})
                            re_dic2.update({'sett':item[8:15].decode(decode_glogal).strip()})
                            futures_account_list.append(re_dic2)
                        else:# item[0:1].decode(decode_glogal) == 'S'
                            re_dic1.update({'comp':item[1:8].decode(decode_glogal).strip()})
                            re_dic1.update({'cosy':item[1:8].decode(decode_glogal).strip()})
                            #re_dic1.update({'cona':NameMapping[item[1:8].decode(decode_glogal).strip()]})
                            re_dic1.update({'cona':item[15:37].decode(decode_glogal).strip()})
                            re_dic1.update({'sett':item[8:15].decode(decode_glogal).strip().rjust(7,'0')})
                            stock_account_list.append(re_dic1)
                    else:#item[37:38].decode(decode_glogal) == 'A'
                        if item[0:1].decode(decode_glogal) == 'F':
                            re_dic2.update({'cosy':item[1:8].decode(decode_glogal).strip()})
                            #re_dic2.update({'cona':NameMapping[item[1:8].decode(decode_glogal).strip()]})
                            re_dic2.update({'cona':item[15:37].decode(decode_glogal).strip()})
                            re_dic2.update({'sett':item[8:15].decode(decode_glogal).strip()})
                            futures_account_list.append(re_dic2)
                        else:# item[0:1].decode(decode_glogal) == 'S'
                            re_dic1.update({'comp':item[1:8].decode(decode_glogal).strip()})
                            re_dic1.update({'cosy':item[1:8].decode(decode_glogal).strip()})
                            #re_dic1.update({'cona':NameMapping[item[1:8].decode(decode_glogal).strip()]})
                            re_dic1.update({'cona':item[15:37].decode(decode_glogal).strip()})
                            re_dic1.update({'sett':item[8:15].decode(decode_glogal).strip().rjust(7,'0')})
                            stock_account_list.append(re_dic1)
        #請注意以下為去掉head跟資料筆數後的長度
        #re_dic.update({'':data[:].decode(decode_glogal).strip()})#客戶資料筆數	char[3]
        #re_dic.update({'':data[:].decode(decode_glogal).strip()})#業務別	char[1]
        #re_dic.update({'':data[1:8].decode(decode_glogal).strip()})#券商代號	char[7]
        #re_dic.update({'':data[8:15].decode(decode_glogal).strip()})#交易帳號	char[7]
        #re_dic.update({'':data[15:37].decode(decode_glogal).strip()})#客戶姓名	char[22]
        #re_dic.update({'':data[37:38].decode(decode_glogal).strip()})#交易盤別	Char[1]
        #re_dic.update({'':data[38:39].decode(decode_glogal).strip()})#是否為電子戶	Char[1]
        #re_dic.update({'':data[39:40].decode(decode_glogal).strip()})#市價委託控管	Char[1]
        #re_dic.update({'':data[40:50].decode(decode_glogal).strip()})#ID	Char[10]
        re_dic.update({'stock_account_list':stock_account_list})
        re_dic.update({'futures_account_list':futures_account_list})
    else:
        re_dic.update({'errorcode':data[26:33].decode(decode_glogal).strip()})
        re_dic.update({'error_msg':ErrorMSG_to_dict()[data[26:33].decode(decode_glogal).strip()]})
    return re_dic
def tran_future_002(data):
    re_dic = {}
    re_dic.update({'code':data[26:33].decode(decode_glogal).strip()})
    re_dic.update({'cause':ErrorMSG_to_dict()[data[26:33].decode(decode_glogal).strip()]})
    return re_dic
def tran_future_004(data):
    re_dic = {}
    #withdrawAccountList = []
    if int.from_bytes(data[49:50],byteorder='little')>0:
        #re_dic.update({'':data[50:57].decode(decode_glogal).strip()})#公司別	char[7]
        re_dic.update({'tradeAccount':data[50:57].decode(decode_glogal).strip()+'|'+data[57:64].decode(decode_glogal).strip()})#客戶帳號	char[7]
        #re_dic.update({'':data[64:65].decode(decode_glogal).strip()})#國內外	char[1]
        #re_dic.update({'':data[65:66].decode(decode_glogal).strip()})#出／入金類型	char[1]
        #re_dic.update({'settleCurrency':data[66:69].decode(decode_glogal).strip()})#幣別	char[3]
        #re_dic.update({'':data[69:72].decode(decode_glogal).strip()})#Web代號	char[3]
        #re_dic.update({'':data[72:78].decode(decode_glogal).strip()})#網路序號	char[6]
        #re_dic.update({'':data[78:85].decode(decode_glogal).strip()})#資料總筆數	char[7]
        #re_dic.update({'':data[85:92].decode(decode_glogal).strip()})#目前筆數	char[7]
        #for i in range(int(data[78:85].decode(decode_glogal).strip())):

        #re_dic1.update({'':data[92:99].decode(decode_glogal).strip()})#公司別	char[7]
        #re_dic1.update({'':data[99:102].decode(decode_glogal).strip()})#ＩＢ	char[3]
        #re_dic1.update({'':data[102:109].decode(decode_glogal).strip()})#客戶帳號	char[7]
        re_dic.update({'currency':data[109:112].decode(decode_glogal).strip()})#幣別	char[3]
        #re_dic1.update({'':data[112:113].decode(decode_glogal).strip()})#類型	char[1]
        re_dic.update({'bankNo':data[113:120].decode(decode_glogal).strip()})#銀行代碼	char[7]
        re_dic.update({'bankAccount':data[120:140].decode(decode_glogal).strip()})#銀行帳號	char[20]
        #re_dic1.update({'':data[140:141].decode(decode_glogal).strip()})#國內外	char[1]
        #withdrawAccountList.append(re_dic)
        #re_dic.update({'withdrawAccountList':withdrawAccountList})
        #re_dic.update({'settleCurrency':"NTD"})
        #re_dic.update({'noticeSign':"YNNNY"})
    else:
        re_dic.update({'code':data[26:33].decode(decode_glogal).strip()})#委託回報代號    Char[7]
        re_dic.update({'cause':ErrorMSG_to_dict()[data[26:33].decode(decode_glogal).strip()]})#委託回報訊息    char[60]
    return re_dic
def tran_future_100(data):
    re_dic = {}
    if len(data) == 0:
        re_dic.update({'code':'1009999'})#委託回報代號    Char[7]
        re_dic.update({'cause':'中菲中台無回應'})#委託回報訊息    char[60]
    elif int.from_bytes(data[49:50],byteorder='little')>0:
        #直接轉換
        re_dic.update({'code':data[126:133].decode(decode_glogal).strip()})#委託回報代號     char[1]
        re_dic.update({'cause':data[133:193].decode(decode_glogal).strip()})#錯誤訊息中文     char[8]
    else:
        re_dic.update({'code':data[26:33].decode(decode_glogal).strip()})#委託回報代號    Char[7]
        re_dic.update({'cause':ErrorMSG_to_dict()[data[26:33].decode(decode_glogal).strip()]})#委託回報訊息    char[60]
    return re_dic
def tran_future_101(data):
    re_dic = {}
    if len(data) == 0:
        re_dic.update({'code':'1019999'})#委託回報代號    Char[7]
        re_dic.update({'cause':'中菲中台無回應'})#委託回報訊息    char[60]
    elif int.from_bytes(data[49:50],byteorder='little')>0:
    #直接轉換
        re_dic.update({'code':data[117:124].decode(decode_glogal).strip()})#委託回報代號    Char[7]
        re_dic.update({'cause':data[124:184].decode(decode_glogal).strip()})#委託回報訊息    char[60]
    else:#int.from_bytes(data[49:50],byteorder='little') == 0:
        re_dic.update({'code':data[26:33].decode(decode_glogal).strip()})#委託回報代號    Char[7]
        re_dic.update({'cause':ErrorMSG_to_dict()[data[26:33].decode(decode_glogal).strip()]})#委託回報訊息    char[60]
    return re_dic
def tran_future_200(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little')>0:
        #re_dic.update({'':data[50:51].decode(decode_glogal).strip()})#市場別	char[1]
        re_dic.update({'41':data[51:54].decode(decode_glogal).strip()})#Web代號	char[3]
        re_dic.update({'42':data[54:60].decode(decode_glogal).strip()})#網路序號	char[6]
        re_dic.update({'3':data[60:67].decode(decode_glogal).strip()})#總筆數	char[7]
        #re_dic.update({'':data[67:74].decode(decode_glogal).strip()})#目前筆數	Char[7]
        #re_dic.update({'':data[74:75].decode(decode_glogal).strip()})#查詢類別	char[1]
        re_dic.update({'5':data[75:82].decode(decode_glogal).strip()})#公司別	char[7]
        re_dic.update({'6':data[82:89].decode(decode_glogal).strip()})#客戶帳號	Char[7]
        re_dic.update({'4':'T3'})#data[89:95].decode(decode_glogal).strip()})#交易所	Char[6]
        #re_dic.update({'':data[89:92].decode(decode_glogal).strip()})#組別	Char[3]
        #re_dic.update({'':data[92:98].decode(decode_glogal).strip()})#交易員	char[6]
        #re_dic.update({'':data[98:104].decode(decode_glogal).strip()})#交易所	char[6]
        re_dic.update({'7':data[104:110].decode(decode_glogal).strip()})#委託書號1	char[6]
        #re_dic.update({'':data[110:120].decode(decode_glogal).strip()})#成交序號1	char[10]
        #re_dic.update({'':data[120:123].decode(decode_glogal).strip()})#拆單序號1	char[3]
        re_dic.update({'8':data[123:131].decode(decode_glogal).strip()})#成交日期1	char[8]
        re_dic.update({'15':data[131:132].decode(decode_glogal).strip()})#買賣別1	char[1]
        re_dic.update({'9':data[132:133].decode(decode_glogal).strip()})#交易種類1	Char[1]
        re_dic.update({'11':data[133:140].decode(decode_glogal).strip()})#商品代號1	Char[7]
        re_dic.update({'47':symb_ch_name_search(data[133:140].decode(decode_glogal).strip())})#商品代號1中文名稱
        re_dic.update({'12':data[140:146].decode(decode_glogal).strip()})#商品年月1	Char[6]
        re_dic.update({'13':data[146:161].decode(decode_glogal).strip()})#履約價1	Char[15]
        re_dic.update({'14':data[161:162].decode(decode_glogal).strip()})#CALL/PUT1	Char[1]
        re_dic.update({'25':data[162:167].decode(decode_glogal).strip()})#未平倉量1	Char[5]
        re_dic.update({'23':data[167:182].decode(decode_glogal).strip()})#結算價1	Char[15]
        re_dic.update({'27':data[182:197].decode(decode_glogal).strip()})#及時價1	Char[15]
        re_dic.update({'29':data[197:212].decode(decode_glogal).strip()})#未平倉損益1	Char[15]
        re_dic.update({'31':data[212:227].decode(decode_glogal).strip()})#原始保證金1	Char[15]
        re_dic.update({'33':data[227:242].decode(decode_glogal).strip()})#維持保證金1	Char[15]
        re_dic.update({'39':data[242:245].decode(decode_glogal).strip()})#幣別1	Char[3]
        re_dic.update({'21':data[245:260].decode(decode_glogal).strip()})#成交價1	Char[15]
        #re_dic.update({'':data[260:266].decode(decode_glogal).strip()})#委託書號2	Char[6]
        #re_dic.update({'':data[266:276].decode(decode_glogal).strip()})#成交序號2	Char[10]
        #re_dic.update({'':data[276:279].decode(decode_glogal).strip()})#拆單序號2	Char[3]
        #re_dic.update({'':data[279:287].decode(decode_glogal).strip()})#成交日期2	Char[8]
        re_dic.update({'20':data[287:288].decode(decode_glogal).strip()})#買賣別2	Char[1]
        #re_dic.update({'':data[288:289].decode(decode_glogal).strip()})#交易種類2	Char[1]
        re_dic.update({'16':data[289:296].decode(decode_glogal).strip()})#商品代號2	Char[7]
        re_dic.update({'48':symb_ch_name_search(data[289:296].decode(decode_glogal).strip())})#商品代號2中文名稱
        re_dic.update({'17':data[296:302].decode(decode_glogal).strip()})#商品年月2	Char[6]
        re_dic.update({'18':data[302:317].decode(decode_glogal).strip()})#履約價2	Char[15]
        re_dic.update({'19':data[317:318].decode(decode_glogal).strip()})#CALL/PUT2	Char[1]
        re_dic.update({'26':data[318:323].decode(decode_glogal).strip()})#未平倉量2	Char[5]
        re_dic.update({'24':data[323:338].decode(decode_glogal).strip()})#結算價2	Char[15]
        re_dic.update({'28':data[338:353].decode(decode_glogal).strip()})#及時價2	Char[15]
        re_dic.update({'30':data[353:368].decode(decode_glogal).strip()})#未平倉損益2 (權利金市值) Char[15]
        re_dic.update({'32':data[368:383].decode(decode_glogal).strip()})#原始保證金2	Char[15]
        re_dic.update({'34':data[383:398].decode(decode_glogal).strip()})#維持保證金2	Char[15]
        #re_dic.update({'':data[398:401].decode(decode_glogal).strip()})#幣別2	Char[3]
        re_dic.update({'22':data[401:416].decode(decode_glogal).strip()})#成交價2	Char[15]
        re_dic.update({'40':data[416:417].decode(decode_glogal).strip()})#當沖碼	Char[1]
        re_dic.update({'10':data[417:418].decode(decode_glogal).strip()})#組合方式	Char[1]
        #re_dic.update({'':data[418:419].decode(decode_glogal).strip()})#來源別1	Char[1]
        #re_dic.update({'':data[419:420].decode(decode_glogal).strip()})#來源別2	Char[1]
        #re_dic.update({'':data[420:438].decode(decode_glogal).strip()})#成交時標的物股數1	Char[18]
        #re_dic.update({'':data[438:449].decode(decode_glogal).strip()})#調整累計現金股利1	Char[11]
        re_dic.update({'43':data[449:457].decode(decode_glogal).strip()})#成交時間1	Char[8]
        re_dic.update({'44':data[457:465].decode(decode_glogal).strip()})#成交時間2	Char[8]
        re_dic.update({'35':data[465:480].decode(decode_glogal).strip()})#參考現值1	Char[15]
        re_dic.update({'36':data[480:495].decode(decode_glogal).strip()})#參考現值2	Char[15]
        #re_dic.update({'':data[495:496].decode(decode_glogal).strip()})#國際合作商品轉入註記1	Char[1]
        #re_dic.update({'':data[496:497].decode(decode_glogal).strip()})#國際合作商品轉入註記2	Char[1]
        re_dic.update({'37':data[497:512].decode(decode_glogal).strip()})#權利金市值1	Char[15]
        re_dic.update({'38':data[512:527].decode(decode_glogal).strip()})#權利金市值2	Char[15]
        re_dic.update({'45':data[527:535].decode(decode_glogal).strip()})#交易方式1	Char[8]
        re_dic.update({'46':data[535:543].decode(decode_glogal).strip()})#交易方式2	Char[8]
        
        re_dic.update({'49':""})#單筆結束旗標
    return re_dic
def tran_future_201_0(data):#單式
    re_dic = {}
    #re_dic.update({'':data[50:51].decode(decode_glogal).strip()})#市場別	Char[1]
    #re_dic.update({'':data[51:54].decode(decode_glogal).strip()})#Web代號	Char[3]
    #re_dic.update({'':data[54:60].decode(decode_glogal).strip()})#網路序號	Char[6]
    re_dic.update({'41':data[51:54].decode(decode_glogal).strip()})#Web代號 Char[3]
    re_dic.update({'42':data[54:60].decode(decode_glogal).strip()})#網路序號	Char[6]
    re_dic.update({'3':data[60:67].decode(decode_glogal).strip()})#總筆數	Char[7]
    #re_dic.update({'':data[67:74].decode(decode_glogal).strip()})#目前筆數	Char[7]
    #re_dic.update({'':data[74:75].decode(decode_glogal).strip()})#查詢類別	Char[1] 1:單式  2:複式  3:全部
    re_dic.update({'5':data[75:82].decode(decode_glogal).strip()})#公司別	Char[7]
    re_dic.update({'6':data[82:89].decode(decode_glogal).strip()})#客戶帳號	Char[7]
    re_dic.update({'4':'T3'})#data[89:95].decode(decode_glogal).strip()})#交易所	Char[6]
    re_dic.update({'7':data[95:101].decode(decode_glogal).strip()})#委託書號1	Char[6]
    #re_dic.update({'':data[101:111].decode(decode_glogal).strip()})#成交序號1	Char[10]
    #re_dic.update({'':data[111:114].decode(decode_glogal).strip()})#拆單序號1	Char[3] 
    re_dic.update({'8':data[114:122].decode(decode_glogal).strip()})#成交日期1	Char[8] 
    re_dic.update({'15':data[122:123].decode(decode_glogal).strip()})#買賣別1	Char[1] 
    #re_dic.update({'':data[123:124].decode(decode_glogal).strip()})#交易種類1	Char[1] 
    re_dic.update({'11':data[124:131].decode(decode_glogal).strip()})#商品代號1	Char[7] 
    re_dic.update({'12':data[131:137].decode(decode_glogal).strip()})#商品年月1	Char[6]
    re_dic.update({'13':str(int(float(data[137:152].decode(decode_glogal).strip()))*10)})#履約價1	Char[15]
    re_dic.update({'14':data[152:153].decode(decode_glogal).strip()})#CALL/PUT1	Char[1]
    re_dic.update({'25':data[153:158].decode(decode_glogal).strip()})#未平倉量1	Char[5]
    re_dic.update({'23':data[158:173].decode(decode_glogal).strip()})#結算價1	Char[15]
    re_dic.update({'27':data[173:188].decode(decode_glogal).strip()})#即時價1	Char[15]
    re_dic.update({'29':data[188:203].decode(decode_glogal).strip()})#未平倉損益1	Char[15]
    #re_dic.update({'':data[203:218].decode(decode_glogal).strip()})#原始保證金1	Char[15]
    #re_dic.update({'':data[218:233].decode(decode_glogal).strip()})#總市值1	Char[15]
    re_dic.update({'39':data[233:236].decode(decode_glogal).strip()})#幣別1	Char[3]
    re_dic.update({'21':data[236:251].decode(decode_glogal).strip()})#成交價1	Char[15]
    #re_dic.update({'':data[251:257].decode(decode_glogal).strip()})#委託書號2	Char[6]
    #re_dic.update({'':data[257:267].decode(decode_glogal).strip()})#成交序號2	Char[10]
    #re_dic.update({'':data[267:270].decode(decode_glogal).strip()})#拆單序號2	Char[3]
    #re_dic.update({'':data[270:278].decode(decode_glogal).strip()})#成交日期2	Char[8]
    #re_dic.update({'':data[278:279].decode(decode_glogal).strip()})#買賣別2	Char[1]
    #re_dic.update({'':data[279:280].decode(decode_glogal).strip()})#交易種類2	Char[1]
    #re_dic.update({'':data[280:287].decode(decode_glogal).strip()})#商品代號2	Char[7]
    #re_dic.update({'':data[287:293].decode(decode_glogal).strip()})#商品年月2	char[6]
    re_dic.update({'18':data[293:308].decode(decode_glogal).strip()})#履約價2	Char[15]
    re_dic.update({'19':data[308:309].decode(decode_glogal).strip()})#CALL/PUT2	Char[1]
    #re_dic.update({'':data[309:314].decode(decode_glogal).strip()})#未平倉量2	Char[5]
    re_dic.update({'24':data[314:329].decode(decode_glogal).strip()})#結算價2	Char[15]
    re_dic.update({'28':data[329:344].decode(decode_glogal).strip()})#即時價2	Char[15]
    re_dic.update({'30':data[344:359].decode(decode_glogal).strip()})#未平倉損益2  (權利金市值) Char[15]
    re_dic.update({'37':data[359:374].decode(decode_glogal).strip()})#原始保證金2	Char[15]

    #re_dic.update({'':data[389:404].decode(decode_glogal).strip()})#總市值2	Char[15]
    #re_dic.update({'':data[404:407].decode(decode_glogal).strip()})#幣別2	Char[3]
    re_dic.update({'22':data[407:422].decode(decode_glogal).strip()})#成交價2	Char[15]
    #re_dic.update({'':data[422:423].decode(decode_glogal).strip()})#當沖碼	Char[1]
    re_dic.update({'10':data[423:424].decode(decode_glogal).strip()})#組合方式	Char[1]
    #re_dic.update({'':data[424:425].decode(decode_glogal).strip()})#來源別1	Char[1]
    #re_dic.update({'':data[425:426].decode(decode_glogal).strip()})#來源別2	Char[1]
    #re_dic.update({'':data[426:431].decode(decode_glogal).strip()})#抵繳口數	Char[5]
    #re_dic.update({'':data[431:436].decode(decode_glogal).strip()})#混合口數	Char[5]
    #re_dic.update({'':data[436:441].decode(decode_glogal).strip()})#當沖口數	Char[5]
    #re_dic.update({'':data[441:446].decode(decode_glogal).strip()})#EUREX轉入量1	Char[5]
    #re_dic.update({'':data[446:451].decode(decode_glogal).strip()})#EUREX轉入量2	Char[5]
    re_dic.update({'33':""})#維持保證金1
    re_dic.update({'34':""})#維持保證金2
    re_dic.update({'35':""})#參考現值1
    re_dic.update({'36':""})#參考現值2
    re_dic.update({'43':""})#成交時間1
    re_dic.update({'44':""})#成交時間2
    re_dic.update({'49':""})#單筆結束旗標
    return re_dic
def tran_future_201_20(data):#複式
    #複式單在大洲欄位後加上 1 2 在製作成xml時 方便區隔
    re_dic = {}
    #re_dic.update({'':data[50:51].decode(decode_glogal).strip()})#市場別	Char[1]       
    #re_dic.update({'':data[51:54].decode(decode_glogal).strip()})#Web代號	Char[3]     
    #re_dic.update({'':data[54:60].decode(decode_glogal).strip()})#網路序號	Char[6]
    re_dic.update({'inse':data[51:54].decode(decode_glogal).strip()+data[54:60].decode(decode_glogal).strip()})#Web代號+網路序號	Char[3]+Char[6]    
    #re_dic.update({'':data[60:67].decode(decode_glogal).strip()})#總筆數	Char[7]       
    #re_dic.update({'':data[67:74].decode(decode_glogal).strip()})#目前筆數	Char[7]     
    #re_dic.update({'':data[74:75].decode(decode_glogal).strip()})#查詢類別	Char[1]     
    #re_dic.update({'':data[75:82].decode(decode_glogal).strip()})#公司別	Char[7]       
    re_dic.update({'sett':data[82:89].decode(decode_glogal).strip()})#客戶帳號	Char[7]
    #re_dic.update({'':data[89:95].decode(decode_glogal).strip()})#交易所	Char[6]
    re_dic.update({'comm':data[95:101].decode(decode_glogal).strip()})#委託書號1	Char[6]
    #re_dic.update({'':data[101:111].decode(decode_glogal).strip()})#成交序號1	Char[10]
    #re_dic.update({'':data[111:114].decode(decode_glogal).strip()})#拆單序號1	Char[3] 
    re_dic.update({'podt':data[114:122].decode(decode_glogal).strip()})#成交日期1	Char[8] 
    re_dic.update({'pomd':data[114:122].decode(decode_glogal).strip()})#成交日期1	Char[8] 
    re_dic.update({'losh':get_bs(data[278:279].decode(decode_glogal).strip())})#買賣別1	Char[1] 
    re_dic.update({'coli':data[123:124].decode(decode_glogal).strip()})#交易種類1	Char[1] 
    #re_dic.update({'':data[124:131].decode(decode_glogal).strip()})#商品代號1	Char[7] 
    re_dic.update({'exdt':data[131:137].decode(decode_glogal).strip()})#商品年月1	Char[6]
    #re_dic.update({'':str(int(float(data[137:152].decode(decode_glogal).strip()))*10)})#履約價1	Char[15]
    if data[122:123].decode(decode_glogal) == 'B':
        re_dic.update({'stpr':'1'})#履約價1	Char[15]    
    else:
        re_dic.update({'stpr':'2'})#履約價1	Char[15]    
    #re_dic.update({'':data[152:153].decode(decode_glogal).strip()})#CALL/PUT1	Char[1]   
    re_dic.update({'lots':data[153:158].decode(decode_glogal).strip()})#未平倉量1	Char[5]   
    re_dic.update({'polt':data[153:158].decode(decode_glogal).strip()})#未平倉量1	Char[5]   
    #re_dic.update({'':data[158:173].decode(decode_glogal).strip()})#結算價1	Char[15]    
    #re_dic.update({'':data[173:188].decode(decode_glogal).strip()})#即時價1	Char[15]    
    #re_dic.update({'':data[188:203].decode(decode_glogal).strip()})#未平倉損益1	Char[15]
    #re_dic.update({'':data[203:218].decode(decode_glogal).strip()})#原始保證金1	Char[15]
    #re_dic.update({'':data[218:233].decode(decode_glogal).strip()})#總市值1	Char[15]    
    #re_dic.update({'':data[233:236].decode(decode_glogal).strip()})#幣別1	Char[3]       
    re_dic.update({'pric':data[236:251].decode(decode_glogal).strip()})#成交價1	Char[15]
    #re_dic.update({'':data[251:257].decode(decode_glogal).strip()})#委託書號2	Char[6]   
    #re_dic.update({'':data[257:267].decode(decode_glogal).strip()})#成交序號2	Char[10]  
    #re_dic.update({'':data[267:270].decode(decode_glogal).strip()})#拆單序號2	Char[3]   
    #re_dic.update({'':data[270:278].decode(decode_glogal).strip()})#成交日期2	Char[8]   

    #re_dic.update({'':data[278:279].decode(decode_glogal).strip()})#買賣別2	Char[1]
    #re_dic.update({'':data[279:280].decode(decode_glogal).strip()})#交易種類2	Char[1]
    #re_dic.update({'':data[280:287].decode(decode_glogal).strip()})#商品代號2	Char[7]
    #re_dic.update({'':data[287:293].decode(decode_glogal).strip()})#商品年月2	char[6]
    #re_dic.update({'':data[293:308].decode(decode_glogal).strip()})#履約價2	Char[15]
    #re_dic.update({'':data[308:309].decode(decode_glogal).strip()})#CALL/PUT2	Char[1]
    #re_dic.update({'':data[309:314].decode(decode_glogal).strip()})#未平倉量2	Char[5]
    #re_dic.update({'':data[314:329].decode(decode_glogal).strip()})#結算價2	Char[15]
    #re_dic.update({'':data[329:344].decode(decode_glogal).strip()})#即時價2	Char[15]
    #re_dic.update({'':data[344:359].decode(decode_glogal).strip()})#未平倉損益2   Char[15]
    #re_dic.update({'':data[359:374].decode(decode_glogal).strip()})#(權利金市值)	Char[15]
    #re_dic.update({'':data[374:389].decode(decode_glogal).strip()})#原始保證金2	Char[15]
    #re_dic.update({'':data[389:404].decode(decode_glogal).strip()})#總市值2	Char[15]
    #re_dic.update({'':data[404:407].decode(decode_glogal).strip()})#幣別2	Char[3]
    #re_dic.update({'':data[407:422].decode(decode_glogal).strip()})#成交價2	Char[15]
    #re_dic.update({'':data[422:423].decode(decode_glogal).strip()})#當沖碼	Char[1]
    #re_dic.update({'':data[423:424].decode(decode_glogal).strip()})#組合方式	Char[1]
    #re_dic.update({'':data[424:425].decode(decode_glogal).strip()})#來源別1	Char[1]
    #re_dic.update({'':data[425:426].decode(decode_glogal).strip()})#來源別2	Char[1]
    #re_dic.update({'':data[426:431].decode(decode_glogal).strip()})#抵繳口數	Char[5]
    #re_dic.update({'':data[431:436].decode(decode_glogal).strip()})#混合口數	Char[5]
    #re_dic.update({'':data[436:441].decode(decode_glogal).strip()})#當沖口數	Char[5]
    #re_dic.update({'':data[441:446].decode(decode_glogal).strip()})#EUREX轉入量1	Char[5]
    #re_dic.update({'':data[446:451].decode(decode_glogal).strip()})#EUREX轉入量2	Char[5]
    return re_dic
def tran_future_202(data):
    re_dic = {}
    #b'\x111515560400000001700202AP12020000               \x00\x8aIDS200088300000020000001F0390008326195       000000            0.0 000000000000000000000000000000000000000000000       0.00000010000000000\n'
    #b'\x111515560560000001700202AP12020000               \x00\x8aIDS200088300000020000002F0390008326195TXF    201605            0.0 000010000000038000000000900000000000001000000    8108.00000010000000000\n'
    re_dic.update({'':data[50:51].decode(decode_glogal).strip()})#市場別	Char[1]
    re_dic.update({'':data[51:54].decode(decode_glogal).strip()})#Web代號	Char[3]
    re_dic.update({'':data[54:60].decode(decode_glogal).strip()})#網路序號	Char[6]
    re_dic.update({'':data[60:67].decode(decode_glogal).strip()})#總筆數	Char[7]
    re_dic.update({'':data[67:74].decode(decode_glogal).strip()})#目前筆數	Char[7]              
    re_dic.update({'':data[74:81].decode(decode_glogal).strip()})#公司別	Char[7]                
    re_dic.update({'':data[81:88].decode(decode_glogal).strip()})#客戶帳號	Char[7]
    re_dic.update({'':data[88:95].decode(decode_glogal).strip()})#商品代號1	Char[7]

    a = ProdConvert.ZhongfeiToDazhou(data[78:98].decode(decode_glogal).strip()#商品代碼         char[20]
                                     ,data[103:104].decode(decode_glogal)#買賣別
                                     ,data[50:51].decode(decode_glogal)#市場別
                                     ,DB_str)

    re_dic.update({'':data[95:101].decode(decode_glogal).strip()})#商品年月1	Char[6]
    re_dic.update({'':data[101:116].decode(decode_glogal).strip()})#履約價1	Char[15]
    re_dic.update({'':data[116:117].decode(decode_glogal).strip()})#CALL/PUT1	Char[1]
    re_dic.update({'':data[117:122].decode(decode_glogal).strip()})#昨日買量	Char [5]
    re_dic.update({'':data[122:127].decode(decode_glogal).strip()})#昨日賣量	Char [5]
    re_dic.update({'':data[127:132].decode(decode_glogal).strip()})#今日委託買量	Char [5]
    re_dic.update({'':data[132:137].decode(decode_glogal).strip()})#今日委託賣量	Char [5]
    re_dic.update({'':data[137:142].decode(decode_glogal).strip()})#今日成交買量	Char [5]
    re_dic.update({'':data[142:147].decode(decode_glogal).strip()})#今日成交賣量	Char [5]
    re_dic.update({'':data[147:152].decode(decode_glogal).strip()})#本日了結口數	Char [5]
    re_dic.update({'':data[152:157].decode(decode_glogal).strip()})#目前留倉買量	Char [5]
    re_dic.update({'':data[157:162].decode(decode_glogal).strip()})#目前留倉賣量	Char [5]
    re_dic.update({'':data[162:177].decode(decode_glogal).strip()})#即時價	Char [15]
    re_dic.update({'':data[177:178].decode(decode_glogal).strip()})#商品類別	Char [1]
    re_dic.update({'':data[178:183].decode(decode_glogal).strip()})#EUREX轉入買量	Char [5]
    re_dic.update({'':data[183:188].decode(decode_glogal).strip()})#EUREX轉入賣量	Char [5]

    #固定值
    re_dic.update({'date':str(int(str(datetime.datetime.now())[0:4])-1911)+"/"+str(datetime.datetime.now())[5:7]+"/"+str(datetime.datetime.now())[8:10]})#交易日期         char[8]

    #固定值區
    re_dic.update({'comp':'15000'})
    re_dic.update({'cosy':cosy_all})
    re_dic.update({'cuna':''})#
    re_dic.update({'mark':'TAIMEX'})#市場別

    #更動
    res_agls = ''
    res_lino = ''
    res_kind = ''
    res_orpt = ''
    res_extr = ''
    res_orcn = ''
    if data[120:121].decode(decode_glogal) == '1':#市場別           char[1]
        res_lino = '1'
        res_kind = '1'
    elif data[120:121].decode(decode_glogal) == '4':
        res_lino = '1'
        res_kind = '10'
    elif data[120:121].decode(decode_glogal) == '2':
        res_lino = '2'
        res_kind = '1'
    elif data[120:121].decode(decode_glogal) == '3':
        res_lino = '2'
        res_kind = '10'
    """
    if data[104:105].decode(decode_glogal) == 'L':#委託方式           char[1]
        res_orpt = '0'
    elif data[104:105].decode(decode_glogal) == 'M':
        res_orpt = '10'
    """
    if data[119:120].decode(decode_glogal) == '0':#沖銷別(開平倉碼) char[1]
        res_extr = '0'
    elif data[119:120].decode(decode_glogal) == '1':
        res_extr = '1'
    elif data[119:120].decode(decode_glogal) == '2':
        res_extr = '4'

    if data[120:121].decode(decode_glogal) == 'R':#委託條件         char[1]
        res_orcn = '0'
    elif data[120:121].decode(decode_glogal) == 'F':
        res_orcn = '10'
    elif data[120:121].decode(decode_glogal) == 'I':
        res_orcn = '20'

    if str(data[103:104].decode(decode_glogal)) == 'B':#買賣別
        res_agls = '1'
    elif str(data[103:104].decode(decode_glogal)) == 'S':
        res_agls = '2'
    re_dic.update({'lino':res_lino})#商品盤別
    re_dic.update({'kind':res_kind})#商品類別
    re_dic.update({'expt':res_orpt})#價格別
    re_dic.update({'extr':res_extr})#委託別
    re_dic.update({'excn':res_orcn})#委託條件
    re_dic.update({'agls':res_agls})#買賣別
    return re_dic
def tran_future_203(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little')>0:
        #re_dic.update({'':data[50:51].decode(decode_glogal).strip()})#市場別	Char(1)
        re_dic.update({'5':data[51:58].decode(decode_glogal).strip()})#公司別	Char(7)
        re_dic.update({'6':data[58:65].decode(decode_glogal).strip()})#客戶帳號	Char(7)
        #re_dic.update({'':data[65:68].decode(decode_glogal).strip()})#Web代號	Char(3)
        #re_dic.update({'':data[68:74].decode(decode_glogal).strip()})#網路序號	Char(6)
        re_dic.update({'3':data[74:81].decode(decode_glogal).strip()})#資料總筆數	Char(7)
        #re_dic.update({'':data[81:88].decode(decode_glogal).strip()})#目前筆數	Char(7)
        re_dic.update({'4':data[88:94].decode(decode_glogal).strip()})#交易所	Char[6]
        re_dic.update({'7':data[94:102].decode(decode_glogal).strip()})#平倉日期	Char[8]
        re_dic.update({'8':data[102:110].decode(decode_glogal).strip()})#平倉成交日期	Char[8]
        re_dic.update({'9':data[110:116].decode(decode_glogal).strip()})#平倉委託編號	Char[6]
        re_dic.update({'10':data[116:126].decode(decode_glogal).strip()})#平倉成交序號	Char[10]
        re_dic.update({'11':data[126:129].decode(decode_glogal).strip()})#平倉拆單序號	Char[3]
        re_dic.update({'12':data[129:137].decode(decode_glogal).strip()})#被平成交日期	Char[8]
        re_dic.update({'13':data[137:143].decode(decode_glogal).strip()})#被平委託編號	Char[6]
        re_dic.update({'14':data[143:153].decode(decode_glogal).strip()})#被平成交序號	Char[10]
        re_dic.update({'15':data[153:156].decode(decode_glogal).strip()})#被平拆單序號	Char[3]
        re_dic.update({'16':data[156:157].decode(decode_glogal).strip()})#指定平倉碼	Char[1]
        re_dic.update({'17':data[157:158].decode(decode_glogal).strip()})#互抵	Char[1]
        re_dic.update({'18':data[158:159].decode(decode_glogal).strip()})#平倉買賣別	Char[1]
        re_dic.update({'19':data[159:166].decode(decode_glogal).strip()})#平倉商品代號	Char[7]
        re_dic.update({'245':symb_ch_name_search(data[159:166].decode(decode_glogal).strip())})#商品中文名稱
        re_dic.update({'20':data[166:172].decode(decode_glogal).strip()})#平倉商品年月	char[6]
        re_dic.update({'21':data[172:187].decode(decode_glogal).strip()})#平倉履約單價	char[15]
        re_dic.update({'22':data[187:188].decode(decode_glogal).strip()})#平倉CALL/PUT	Char[1]
        #re_dic.update({'':data[188:195].decode(decode_glogal).strip())#被平商品代號	Char[7]
        re_dic.update({'23':data[195:200].decode(decode_glogal).strip()})#平倉口數	char[5]
        re_dic.update({'24':data[200:205].decode(decode_glogal).strip()})#被平口數	char[5]
        re_dic.update({'25':data[205:220].decode(decode_glogal).strip()})#平倉成交價	char[15]
        re_dic.update({'26':data[220:235].decode(decode_glogal).strip()})#被平成交價	char[15]
        re_dic.update({'32':data[235:250].decode(decode_glogal).strip()})#平倉損益	char[15]
        #re_dic.update({'':data[250:256].decode(decode_glogal).strip()})#業務員代號	Char[6]
        re_dic.update({'27':data[256:259].decode(decode_glogal).strip()})#幣別	Char[3]
        re_dic.update({'34':data[259:260].decode(decode_glogal).strip()})#平倉當沖碼	Char[1]
        re_dic.update({'35':data[260:261].decode(decode_glogal).strip()})#被平當沖碼	Char[1]
        re_dic.update({'28':data[261:272].decode(decode_glogal).strip()})#平倉手續費	char[11]
        re_dic.update({'29':data[272:283].decode(decode_glogal).strip()})#平倉交易稅	char[11]
        #re_dic.update({'':data[283:284].decode(decode_glogal).strip()})#平倉來源別	Char[1]
        #re_dic.update({'':data[284:285].decode(decode_glogal).strip()})#被平來源別	Char[1]
        #re_dic.update({'':data[285:286].decode(decode_glogal).strip()})#平倉交易種類	Char[1]
        #re_dic.update({'':data[286:287].decode(decode_glogal).strip()})#被平交易種類	Char[1]
        re_dic.update({'36':data[287:288].decode(decode_glogal).strip()})#平倉到期判別碼	Char[1]
        re_dic.update({'33':data[288:303].decode(decode_glogal).strip()})#淨損益	char[15]
        #re_dic.update({'':data[303:325].decode(decode_glogal)}.strip()})#平倉序號	Char[22]
        re_dic.update({'30':data[325:336].decode(decode_glogal).strip()})#被平手續費	char[11]
        re_dic.update({'31':data[336:347].decode(decode_glogal).strip()})#被平交易稅	char[11]
        re_dic.update({'37':data[347:362].decode(decode_glogal).strip()})#平倉權利金金額	char[15]
        re_dic.update({'38':data[362:377].decode(decode_glogal).strip()})#被平倉權利金金額	char[15]
        re_dic.update({'39':data[377:385].decode(decode_glogal).strip()})#平倉交易方式	Char[8]
        re_dic.update({'40':data[385:393].decode(decode_glogal).strip()})#被平交易方式	Char[8]
        re_dic.update({'49':""})#單筆結束旗標
    return re_dic
def tran_future_204(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little')>0:
        #re_dic.update({'3':data[50:57].decode(decode_glogal)})#資料總筆數       char[7] 
        #re_dic.update({'':data[57:64].decode(decode_glogal)})#目前筆數         char[7] 
        #re_dic.update({'':data[64:65].decode(decode_glogal)})#市場別	Char(1)
        re_dic.update({'5':data[65:72].decode(decode_glogal)})#公司別	Char(7)
        re_dic.update({'6':data[72:79].decode(decode_glogal).strip()})#客戶帳號	Char(7)
        re_dic.update({'4':data[79:85].decode(decode_glogal).strip()})#交易所	Char[6]
        re_dic.update({'7':data[85:93].decode(decode_glogal).strip()})#平倉日期	Char[8]
        re_dic.update({'8':data[93:101].decode(decode_glogal).strip()})#平倉成交日期	Char[8]
        re_dic.update({'9':data[101:107].decode(decode_glogal).strip()})#平倉委託編號	Char[6]
        re_dic.update({'10':data[107:117].decode(decode_glogal).strip()})#平倉成交序號	Char[10]
        re_dic.update({'11':data[117:120].decode(decode_glogal).strip()})#平倉拆單序號	Char[3]
        re_dic.update({'12':data[120:128].decode(decode_glogal).strip()})#被平成交日期	Char[8]
        re_dic.update({'13':data[128:134].decode(decode_glogal).strip()})#被平委託編號	Char[6]
        re_dic.update({'14':data[134:144].decode(decode_glogal).strip()})#被平成交序號	Char[10]
        re_dic.update({'15':data[144:147].decode(decode_glogal).strip()})#被平拆單序號	Char[3]
        re_dic.update({'16':data[147:148].decode(decode_glogal).strip()})#指定平倉碼	Char[1]
        re_dic.update({'17':data[148:149].decode(decode_glogal).strip()})#互抵	Char[1]
        re_dic.update({'18':data[149:150].decode(decode_glogal).strip()})#平倉買賣別	Char[1]
        re_dic.update({'19':data[150:157].decode(decode_glogal).strip()})#平倉商品代號	Char[7]
        re_dic.update({'245':symb_ch_name_search(data[150:157].decode(decode_glogal).strip())})#商品中文名稱
        re_dic.update({'20':data[157:163].decode(decode_glogal).strip()})#平倉商品年月	char[6]
        re_dic.update({'21':data[163:178].decode(decode_glogal).strip()})#平倉履約單價	char[15]
        re_dic.update({'22':data[178:179].decode(decode_glogal).strip()})#平倉CALL/PUT	Char[1]
        #re_dic.update({'':data[179:186].decode(decode_glogal)}.strip())#被平商品代號	Char[7]
        re_dic.update({'23':data[186:191].decode(decode_glogal).strip()})#平倉口數	char[5]
        re_dic.update({'24':data[191:196].decode(decode_glogal).strip()})#被平口數	char[5]
        re_dic.update({'25':data[196:211].decode(decode_glogal).strip()})#平倉成交價	char[15]
        re_dic.update({'26':data[211:226].decode(decode_glogal).strip()})#被平成交價	char[15]
        re_dic.update({'32':data[226:241].decode(decode_glogal).strip()})#平倉損益	char[15]
        #re_dic.update({'':data[241:247].decode(decode_glogal)}.strip())#業務員代號	Char[6]
        re_dic.update({'27':data[247:250].decode(decode_glogal).strip()})#幣別	Char[3]
        re_dic.update({'34':data[250:251].decode(decode_glogal).strip()})#平倉當沖碼	Char[1]
        re_dic.update({'35':data[251:252].decode(decode_glogal).strip()})#被平當沖碼	Char[1]
        re_dic.update({'28':data[252:263].decode(decode_glogal).strip()})#平倉手續費	char[11]
        re_dic.update({'29':data[263:274].decode(decode_glogal).strip()})#平倉交易稅	char[11]
        #re_dic.update({'':data[274:275].decode(decode_glogal).strip()})#平倉來源別	Char[1]
        #re_dic.update({'':data[275:276].decode(decode_glogal).strip()})#被平來源別	Char[1]
        #re_dic.update({'':data[276:277].decode(decode_glogal).strip()})#平倉交易種類	Char[1]
        #re_dic.update({'':data[277:278].decode(decode_glogal).strip()})#被平交易種類	Char[1]
        re_dic.update({'36':data[278:279].decode(decode_glogal).strip()})#平倉到期判別碼	Char[1]
        re_dic.update({'33':data[279:294].decode(decode_glogal).strip()})#淨損益	char[15]
        #re_dic.update({'':data[294:316].decode(decode_glogal).strip()})#平倉序號	Char[22]
        re_dic.update({'30':data[316:327].decode(decode_glogal).strip()})#被平手續費	char[11]
        re_dic.update({'31':data[327:338].decode(decode_glogal).strip()})#被平交易稅	char[11]
        re_dic.update({'37':data[338:353].decode(decode_glogal).strip()})#平倉權利金金額	char[15]
        re_dic.update({'38':data[353:368].decode(decode_glogal).strip()})#被平倉權利金金額	char[15]
        re_dic.update({'39':data[368:376].decode(decode_glogal).strip()})#平倉交易方式	Char[8]
        re_dic.update({'40':data[376:384].decode(decode_glogal).strip()})#被平交易方式	Char[8]
        re_dic.update({'49':""})#單筆結束旗標
    else:
        re_dic.update({'code':data[26:33].decode(decode_glogal).strip()})#委託回報代號    Char[7]
        re_dic.update({'cause':ErrorMSG_to_dict()[data[26:33].decode(decode_glogal).strip()]})#委託回報訊息    char[60]
    return re_dic
def tran_future_207(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little') > 0:
        #re_dic.update({'':data[50:51].decode(decode_glogal).strip()})#市埸別	Char[1]
        re_dic.update({'5':data[51:58].decode(decode_glogal).strip()})#公司別	Char[7]
        re_dic.update({'6':data[58:65].decode(decode_glogal).strip()})#外帳帳號	Char[7]
        #re_dic.update({'':data[65:68].decode(decode_glogal).strip()})#組別	Char[3]
        #re_dic.update({'':data[68:74].decode(decode_glogal).strip()})#交易員	Char[6]
        #re_dic.update({'':data[74:77].decode(decode_glogal).strip()})#Web代號	Char[3]
        #re_dic.update({'':data[77:83].decode(decode_glogal).strip()})#網路序號	Char[6]
        re_dic.update({'3':data[83:90].decode(decode_glogal).strip()})#資料總筆數	char[7]
        re_dic.update({'4':'T3'})#資料總筆數	char[7]
        #re_dic.update({'':data[90:97].decode(decode_glogal).strip()})#目前筆數	char[7]
        #re_dic.update({'':data[97:100].decode(decode_glogal).strip()})#查詢幣別	Char[3]
        re_dic.update({'7':data[100:103].decode(decode_glogal).strip()})#幣別	Char[3]
        re_dic.update({'8':data[103:118].decode(decode_glogal).strip()})#昨日帳款餘額	char[15]
        re_dic.update({'9':data[118:133].decode(decode_glogal).strip()})#手續費	char[15]
        re_dic.update({'10':data[133:148].decode(decode_glogal).strip()})#匯率	char[15]
        re_dic.update({'11':data[148:163].decode(decode_glogal).strip()})#期交稅	char[15]
        re_dic.update({'12':data[163:178].decode(decode_glogal).strip()})#存提金額	char[15]
        re_dic.update({'13':data[178:193].decode(decode_glogal).strip()})#平倉損益	char[15]    
        re_dic.update({'14':data[193:208].decode(decode_glogal).strip()})#未平倉損益	char[15]
        re_dic.update({'15':data[208:223].decode(decode_glogal).strip()})#買方選擇權市值	char[15]
        re_dic.update({'16':data[223:238].decode(decode_glogal).strip()})#賣方選擇權市值	char[15]
        re_dic.update({'17':data[238:253].decode(decode_glogal).strip()})#下單預扣權利金(委託權利金)	char[15]
        re_dic.update({'18':data[253:268].decode(decode_glogal).strip()})#當日權利金收支	char[15]
        re_dic.update({'19':data[268:283].decode(decode_glogal).strip()})#權益數	char[15]
        re_dic.update({'20':data[283:298].decode(decode_glogal).strip()})#原始保證金	char[15]
        re_dic.update({'21':data[298:313].decode(decode_glogal).strip()})#維持保證金	char[15]
        re_dic.update({'22':data[313:328].decode(decode_glogal).strip().replace('-','')})#可用餘額	char[15]	
        re_dic.update({'23':data[328:343].decode(decode_glogal).strip().replace('-','')})#超額/追繳保證金		char[15]
        re_dic.update({'24':data[343:358].decode(decode_glogal).strip().replace('-','')})#當日委託保證金	char[15]
        re_dic.update({'25':data[358:373].decode(decode_glogal).strip().replace('-','')})#履約損益 	char[15]
        re_dic.update({'26':data[373:388].decode(decode_glogal).strip()})#變動權利金	char[15]
        re_dic.update({'27':data[388:394].decode(decode_glogal).strip()})#洗價時間	Char[6]
        re_dic.update({'28':data[394:409].decode(decode_glogal).strip()})#期貨足額原始保證金	char[15]
        re_dic.update({'29':data[409:424].decode(decode_glogal).strip()})#期貨足額維持保證金	char[15]
        re_dic.update({'30':data[424:439].decode(decode_glogal).strip()})#期貨減收原始保證金	char[15]
        re_dic.update({'31':data[439:454].decode(decode_glogal).strip()})#期貨減收維持保證金	char[15]
        re_dic.update({'32':data[454:462].decode(decode_glogal).strip()})#足額風險係數%	char[8]
        re_dic.update({'33':data[462:477].decode(decode_glogal).strip()})#依「加收保證金指標」所加收之保證金	char[15]
        re_dic.update({'34':data[477:485].decode(decode_glogal).strip()})#維持率%	char[8]
        re_dic.update({'35':data[485:500].decode(decode_glogal).strip()})#期貨當沖原始保證金	char[15]
        re_dic.update({'36':data[500:515].decode(decode_glogal).strip()})#期貨當沖維持保證金	char[15]
        re_dic.update({'37':data[515:530].decode(decode_glogal).strip()})#權利金市值(買方+賣方)		char[15]
        re_dic.update({'38':data[530:538].decode(decode_glogal).strip()})#總市值風險係數%	char[8]
        re_dic.update({'39':data[538:553].decode(decode_glogal).strip()})#本日盤中浮動損益	char[15]
        re_dic.update({'40':data[553:568].decode(decode_glogal).strip()})#權益總值	char[15]
        re_dic.update({'41':data[568:583].decode(decode_glogal).strip()})#權益總值追繳金額	char[15]
        re_dic.update({'42':data[583:598].decode(decode_glogal).strip()})#本日餘額	char[15]
        re_dic.update({'43':data[598:613].decode(decode_glogal).strip()})#有價證券抵繳總額	char[15]
        re_dic.update({'44':data[613:628].decode(decode_glogal).strip()})#可動用(不含CN$超額)保證金	char[15]
        re_dic.update({'45':data[628:643].decode(decode_glogal).strip()})#未沖銷選擇權浮動損益	char[15]
        re_dic.update({'46':data[643:658].decode(decode_glogal).strip()})#契約調整權益數加/減項	char[15]
        re_dic.update({'47':data[658:673].decode(decode_glogal).strip()})#出金	char[15]
        re_dic.update({'48':data[673:688].decode(decode_glogal).strip()})#入金	char[15]
        #re_dic.update({'':data[688:703].decode(decode_glogal).strip()})#委託權利金	char[15]
        #re_dic.update({'':data[703:718].decode(decode_glogal).strip()})#圈存金額	char[15]
        re_dic.update({'49':""})#單筆結束旗標
    else:
        re_dic.update({'code':data[26:33].decode(decode_glogal).strip()})#委託回報代號    Char[7]
        re_dic.update({'cause':ErrorMSG_to_dict()[data[26:33].decode(decode_glogal).strip()]})#委託回報訊息    char[60]
    return re_dic
def tran_future_208(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little')>0:
        #data[57:64].decode(decode_glogal) < int(data[50:57].decode(decode_glogal))
        #re_dic.update({'':data[50:57].decode(decode_glogal)})#資料總筆數       char[7] 
        #re_dic.update({'':data[57:64].decode(decode_glogal)})#目前筆數         char[7] 
        #re_dic.update({'':data[64:71].decode(decode_glogal)})#期貨商代號       char[7] 
        re_dic.update({'sett':data[71:78].decode(decode_glogal).strip()})#投資人帳號       char[7] 
        #商品代碼轉換
        try:
            a = ProdConvert.ZhongfeiToDazhou(data[78:98].decode(decode_glogal).strip()#商品代碼         char[20]
                                             ,data[103:104].decode(decode_glogal)#買賣別
                                             ,data[134:135].decode(decode_glogal)#市場別
                                             ,DB_str)
            re_dic.update({'symb':data[78:98].decode(decode_glogal).strip()})#商品代碼a.symb
            re_dic.update({'exdt':a.exdt})#履約日(第一隻腳)
            re_dic.update({'losh':a.losh})#買賣別(第一隻腳)
            re_dic.update({'capu':a.capu})#權利別(第一隻腳)
            #lots   成交口數(第一隻腳)
            #pric   成交價(第一隻腳)
            re_dic.update({'stpr':a.stpr})#履約價(第一隻腳)
            re_dic.update({'seed':a.seed})#履約日(第二隻腳)
            #selt   成交口數(第二隻腳)
            #sepr   成交價(第二隻腳)
            re_dic.update({'sesp':a.sesp})#履約價(第二隻腳)
            re_dic.update({'secp':a.secp})#權利別(第二隻腳)
            re_dic.update({'sels':a.sels})#買賣別(第二隻腳)
            re_dic.update({'agsy':data[78:98].decode(decode_glogal).strip()})#a.symb+a.Date1+a.Date2
        except:
            re_dic.update({'symb':data[78:98].decode(decode_glogal).strip()})#商品代碼
            re_dic.update({'exdt':''})#履約日(第一隻腳)
            re_dic.update({'losh':''})#買賣別(第一隻腳)
            re_dic.update({'capu':''})#權利別(第一隻腳)
            #lots   成交口數(第一隻腳)
            #pric   成交價(第一隻腳)
            re_dic.update({'stpr':''})#履約價(第一隻腳)
            re_dic.update({'seed':''})#履約日(第二隻腳)
            #selt   成交口數(第二隻腳)
            #sepr   成交價(第二隻腳)
            re_dic.update({'sesp':''})#履約價(第二隻腳)
            re_dic.update({'secp':''})#權利別(第二隻腳)
            re_dic.update({'sels':''})#買賣別(第二隻腳)
            re_dic.update({'agsy':data[78:98].decode(decode_glogal).strip()})#
        re_dic.update({'symbname':symb_ch_name_search(data[78:98].decode(decode_glogal).strip())})#商品中文名稱
        re_dic.update({'comm':data[98:103].decode(decode_glogal).strip()})#委託書號         Char[5] 
        re_dic.update({'losh':data[103:104].decode(decode_glogal)})#買賣別           char[1] 
        re_dic.update({'orpt':data[104:105].decode(decode_glogal)})#委託方式         char[1] 
        re_dic.update({'orpr':data[105:116].decode(decode_glogal).strip()})#委託價格         Char[11]
        #re_dic.update({'nepr':data[105:116].decode(decode_glogal).strip()})#委託價格         Char[11]
        re_dic.update({'orsh':data[116:120].decode(decode_glogal).strip()})#委託數量         Char[4] 

        """
        orsh='5' orpr='8700'#改價/量之前
        nesh='5' nepr='8600'#這兩個都是改過後
        duor='8700'#改價之前
        dura='8600'#改價後
        """

        re_dic.update({'orcn':data[120:121].decode(decode_glogal)})#委託條件         char[1] 
        re_dic.update({'ortr':data[121:122].decode(decode_glogal)})#沖銷別(開平倉碼) char[1] 
        re_dic.update({'UnfilledQty':data[122:126].decode(decode_glogal).strip()})#在途數量         char[4] 
        re_dic.update({'DealQty':data[126:130].decode(decode_glogal).strip()})#成交數量         char[4] 
        re_dic.update({'nesh':str(int(data[122:126].decode(decode_glogal).strip())+int(data[126:130].decode(decode_glogal).strip()))})#在途數量+成交數量
        re_dic.update({'DelQty':data[130:134].decode(decode_glogal).strip()})#刪單數量         char[4] 
        re_dic.update({'lino':data[134:135].decode(decode_glogal)})#市場別           char[1] 
        re_dic.update({'OrderTime':data[135:143].decode(decode_glogal)})#委託接收時間     char[8] 
        re_dic.update({'OrderErrCode':data[143:150].decode(decode_glogal)})#委託回報代號     Char[7] 
        re_dic.update({'OrderErrMesg':data[150:210].decode(decode_glogal).strip()})#委託回報訊息     char[60]
        re_dic.update({'orst':data[210:211].decode(decode_glogal)})#委託單類別       char[1] 
        re_dic.update({'InputSource2':data[211:214].decode(decode_glogal)})#原委託WEB代號    Char[3]
        re_dic.update({'orse':data[214:222].decode(decode_glogal)})#原委託流水序號   char[8]
        #re_dic.update({'orse':data[211:214].decode(decode_glogal).strip()+data[214:222].decode(decode_glogal).strip()})#原委託WEB代號+原委託流水序號
        #re_dic.update({'':data[222:223].decode(decode_glogal)})#來源別           char[1] 
        re_dic.update({'date':data[223:231].decode(decode_glogal)})#交易日期         char[8]

        re_dic.update({'duov':str(data[116:120].decode(decode_glogal).strip())})
        re_dic.update({'duva':str(int(data[122:126].decode(decode_glogal))+int(data[126:130].decode(decode_glogal)))})
        re_dic.update({'duor':str(float(data[105:116].decode(decode_glogal).strip()))})
        re_dic.update({'dura':str(float(data[105:116].decode(decode_glogal).strip()))})
        #re_dic.update({'date':str(int(str(data[223:231].decode(decode_glogal))[0:4])-1911)+"/"+str(data[223:231].decode(decode_glogal))[4:6]+"/"+str(data[223:231].decode(decode_glogal))[6:8]})#交易日期         char[8]
    #固定值區
    re_dic.update({'comp':'15000'})
    re_dic.update({'cosy':cosy_all})
    re_dic.update({'mark':'TAIMEX'})#市場別
    #re_dic.update({'symbname':''})#商品中文名稱
    re_dic.update({'Exchange':'T3'})#??
    re_dic.update({'InputSource':'a'})#??
    re_dic.update({'DealPrice':'0'})#看起來像是成交價格
    re_dic.update({'RecordEndFlag':""})#單筆結束旗標
    re_dic.update({'isHistory':False})
    return re_dic
def tran_future_209(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little')>0:
        #re_dic.update({'':data[50:57].decode(decode_glogal)})#資料總筆數        char[7] 
        #re_dic.update({'':data[57:64].decode(decode_glogal)})#目前筆數          char[7] 
        #re_dic.update({'':data[64:71].decode(decode_glogal)})#期貨商代號        char[7] 
        re_dic.update({'203':data[71:78].decode(decode_glogal).strip()})#投資人帳號        char[7] 
        #re_dic.update({'':data[78:98].decode(decode_glogal)})#商品代碼          char[20]
        a = ProdConvert.ZhongfeiToDazhou(data[78:98].decode(decode_glogal).strip()#商品代碼         char[20]
                                         ,data[103:104].decode(decode_glogal).strip()#買賣別
                                         ,data[120:121].decode(decode_glogal).strip()#市場別
                                         ,DB_str)
        re_dic.update({'222':data[78:98].decode(decode_glogal).strip()})#商品代碼
        re_dic.update({'245':symb_ch_name_search(data[78:98].decode(decode_glogal).strip())})#商品中文名稱
        re_dic.update({'exdt':a.exdt})#履約日(第一隻腳)
        re_dic.update({'227':a.losh})#買賣別(第一隻腳)
        re_dic.update({'capu':a.capu})#權利別(第一隻腳)
        #lots   成交口數(第一隻腳)
        #pric   成交價(第一隻腳)
        re_dic.update({'stpr':a.stpr})#履約價(第一隻腳)
        re_dic.update({'seed':a.seed})#履約日(第二隻腳)
        #selt   成交口數(第二隻腳)
        #sepr   成交價(第二隻腳)
        re_dic.update({'sesp':a.sesp})#履約價(第二隻腳)
        re_dic.update({'secp':a.secp})#權利別(第二隻腳)
        re_dic.update({'214':a.sels})#買賣別(第二隻腳)
        #re_dic.update({'agsy':data[78:98].decode(decode_glogal).strip()})#a.symb+a.Date1+a.Date2
        re_dic.update({'comm':data[98:103].decode(decode_glogal).strip()})#委託書號          Char[5] 
        re_dic.update({'209':data[103:104].decode(decode_glogal)})#買賣別
        re_dic.update({'262':str(data[104:115].decode(decode_glogal).strip())})#成交價格/成交價差 Char[11]#20160523 修改
        #re_dic.update({'lots':data[115:119].decode(decode_glogal)})#成交數量          Char[4] 
        re_dic.update({'261':data[115:119].decode(decode_glogal).strip()})#成交數量          Char[4] 
        re_dic.update({'220':data[119:120].decode(decode_glogal)})#沖銷別(開平倉碼)  char[1] 
        re_dic.update({'204':data[120:121].decode(decode_glogal)})#市場別            char[1] 
        re_dic.update({'260':data[121:129].decode(decode_glogal)})#成交時間          char[8] 
        re_dic.update({'exse':data[129:137].decode(decode_glogal)})#回報序號          char[8] 
        #re_dic.update({'':data[137:147].decode(decode_glogal)})#商品代碼1         char[10]
        #re_dic.update({'':data[147:148].decode(decode_glogal)})#買賣別1           char[1] 
        re_dic.update({'267':data[148:159].decode(decode_glogal).strip()})#成交價格1         Char[11]
        re_dic.update({'lots':data[159:163].decode(decode_glogal).strip()})#成交數量1         Char[4] 
        #re_dic.update({'':data[163:173].decode(decode_glogal)})#商品代碼2         char[10]
        #re_dic.update({'':data[173:174].decode(decode_glogal)})#買賣別2           char[1] 
        re_dic.update({'268':data[174:185].decode(decode_glogal).strip()})#成交價格2         Char[11]
        re_dic.update({'selt':data[185:189].decode(decode_glogal).strip()})#成交數量2         Char[4] 
        #re_dic.update({'':data[189:190].decode(decode_glogal)})#複式單類別        Char[1] 
        #re_dic.update({'':data[190:193].decode(decode_glogal)})#WEB代號           Char[3] 
        #re_dic.update({'':data[193:201].decode(decode_glogal)})#流水序號          Char[8] 
        #re_dic.update({'269':data[190:193].decode(decode_glogal).strip()+data[193:201].decode(decode_glogal).strip()})#原委託WEB代號+原委託流水序號
        re_dic.update({'240':data[201:209].decode(decode_glogal).strip()})#交易日期          char[8] 
        #re_dic.update({'':data[209:210].decode(decode_glogal).strip()})#20170517 委託單狀態 0:預約單、1盤中單(早盤)、2盤後單
        re_dic.update({'RecordEndFlag':""})#單筆結束旗標
        re_dic.update({'isHistory':False})
    return re_dic
def tran_future_211(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little')>0:
        #re_dic.update({'':data[50:57].decode(decode_glogal)})#資料總筆數	char[7]
        #re_dic.update({'':data[57:64].decode(decode_glogal)})#目前筆數	char[7]
        #re_dic.update({'':data[64:71].decode(decode_glogal)})#期貨商代號	char[7]
        re_dic.update({'sett':data[71:78].decode(decode_glogal).strip()})#投資人帳號	char[7]
        re_dic.update({'symb':data[78:98].decode(decode_glogal).strip()})#商品代碼	char[20]
        re_dic.update({'symbname':symb_ch_name_search(data[78:98].decode(decode_glogal).strip())})#商品中文名稱
        re_dic.update({'comm':data[98:103].decode(decode_glogal)})#委託書號	Char[5]
        re_dic.update({'losh':data[103:104].decode(decode_glogal)})#買賣別	char[1]
        re_dic.update({'orpt':data[104:105].decode(decode_glogal)})#委託方式	char[1]
        re_dic.update({'orpr':data[105:116].decode(decode_glogal).strip()})#委託價格	Char[11]
        re_dic.update({'orsh':data[116:120].decode(decode_glogal).strip()})#委託數量	Char[4]
        re_dic.update({'orcn':data[120:121].decode(decode_glogal)})#委託條件	char[1]
        re_dic.update({'ortr':data[121:122].decode(decode_glogal)})#沖銷別(開平倉碼)	char[1]
        re_dic.update({'UnfilledQty':data[122:126].decode(decode_glogal).strip()})#在途數量	char[4]
        re_dic.update({'DealQty':data[126:130].decode(decode_glogal).strip()})#成交數量	char[4]
        re_dic.update({'nesh':str(int(data[122:126].decode(decode_glogal).strip())+int(data[126:130].decode(decode_glogal).strip()))})#在途數量+成交數量
        re_dic.update({'DelQty':data[130:134].decode(decode_glogal).strip()})#刪單數量	char[4]
        re_dic.update({'lino':data[134:135].decode(decode_glogal)})#市場別	char[1]
        re_dic.update({'OrderTime':data[135:143].decode(decode_glogal)})#委託接收時間	char[8]
        re_dic.update({'OrderErrCode':data[143:150].decode(decode_glogal).strip()})#委託回報代號	Char[7]
        re_dic.update({'OrderErrMesg':data[150:210].decode(decode_glogal).strip()})#委託回報訊息	char[60]
        re_dic.update({'orst':data[210:211].decode(decode_glogal)})#委託單類別	char[1]
        re_dic.update({'InputSource2':data[211:214].decode(decode_glogal)})#原委託WEB代號	Char[3]
        re_dic.update({'orse':data[214:222].decode(decode_glogal)})#原委託流水序號	char[8]
        #re_dic.update({'':data[222:223].decode(decode_glogal)})#來源別	char[1]
        re_dic.update({'date':data[223:231].decode(decode_glogal).strip()})#交易日期	char[8]
    re_dic.update({'Exchange':'T3'})#??
    re_dic.update({'InputSource':'a'})#??
    re_dic.update({'DealPrice':'0'})#看起來像是成交價格
    re_dic.update({'isHistory':True})
    return re_dic
def tran_future_212(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little') > 0:
        #re_dic.update({'':data[50:57].decode(decode_glogal)})#資料總筆數	char[7]
        #re_dic.update({'':data[57:64].decode(decode_glogal)})#目前筆數	char[7]
        #re_dic.update({'':data[64:71].decode(decode_glogal)})#期貨商代號	char[7]
        re_dic.update({'203':data[71:78].decode(decode_glogal).strip()})#投資人帳號	char[7]
        re_dic.update({'222':data[78:98].decode(decode_glogal).strip()})#商品代碼	char[20]
        re_dic.update({'245':symb_ch_name_search(data[78:98].decode(decode_glogal).strip())})#商品中文名稱
        a = ProdConvert.ZhongfeiToDazhou(data[78:98].decode(decode_glogal).strip()#商品代碼         char[20]
                                         ,data[103:104].decode(decode_glogal).strip()#買賣別
                                         ,data[120:121].decode(decode_glogal).strip()#市場別
                                         ,DB_str)
        re_dic.update({'227':a.losh})#買賣別(第一隻腳)
        re_dic.update({'214':a.sels})#買賣別(第二隻腳)
        re_dic.update({'comm':data[98:103].decode(decode_glogal)})#委託書號	Char[5]
        re_dic.update({'209':data[103:104].decode(decode_glogal)})#買賣別	char[1]
        re_dic.update({'262':data[104:115].decode(decode_glogal).strip()})#成交價格/成交價差	Char[11]
        re_dic.update({'261':data[115:119].decode(decode_glogal).strip()})#成交數量	Char[4]
        re_dic.update({'220':data[119:120].decode(decode_glogal)})#沖銷別(開平倉碼)	char[1]
        re_dic.update({'204':data[120:121].decode(decode_glogal)})#市場別	char[1]
        re_dic.update({'260':data[121:129].decode(decode_glogal)})#成交時間	char[8]
        re_dic.update({'exse':data[129:137].decode(decode_glogal).strip()})#回報序號	char[8]
        #re_dic.update({'':data[137:147].decode(decode_glogal)})#商品代碼1	char[10]
        #re_dic.update({'':data[147:148].decode(decode_glogal)})#買賣別1	char[1]
        re_dic.update({'267':data[148:159].decode(decode_glogal).strip()})#成交價格1	Char[11]
        re_dic.update({'lots':data[159:163].decode(decode_glogal).strip()})#成交數量1	Char[4]
        #re_dic.update({'':data[163:173].decode(decode_glogal)})#商品代碼2	char[10]
        #re_dic.update({'':data[173:174].decode(decode_glogal)})#買賣別2	char[1]
        re_dic.update({'268':data[174:185].decode(decode_glogal).strip()})#成交價格2	Char[11]
        re_dic.update({'selt':data[185:189].decode(decode_glogal).strip()})#成交數量2	Char[4]
        #re_dic.update({'':data[189:190].decode(decode_glogal)})#複式單類別	Char[1]
        #re_dic.update({'':data[190:193].decode(decode_glogal)})#WEB代號	Char[3]
        #re_dic.update({'':data[193:201].decode(decode_glogal)})#流水序號	Char[8]
        re_dic.update({'240':data[201:209].decode(decode_glogal).strip()})#交易日期	char[8]
        #re_dic.update({'':data[209:210].decode(decode_glogal)})#委託單類別	char[1]
        re_dic.update({'RecordEndFlag':""})#單筆結束旗標
    re_dic.update({'isHistory':True})
    return re_dic
def tran_future_306(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little') > 0:
        if data[107:111].decode(decode_glogal).strip() not in ['D000']:
            re_dic.update({'code':data[107:111].decode(decode_glogal)})#回報狀態	Char[4]
            re_dic.update({'description':data[152:250].decode(decode_glogal).strip()})#註記	Char[98]
        else:
            re_dic.update({'code':'0'})
            re_dic.update({"description":"委託成功"})
    else:
        re_dic.update({'code':'3060001'})#回報狀態	Char[4]
        re_dic.update({'cause':'驗章失敗'})#註記	Char[98]
        re_dic.update({'action':'驗章失敗'})
    """
    DZ 大洲
    0.收到10.已傳送後台 30.取消 90.失敗

    ZF 中菲
    D000-成功
    D001-餘額不足
    D002-出金時間已過
    D003-重複出金
    D004-無此客戶帳號
    D005-無此銀行帳號
    D006-取消出金失敗，無此筆申請
    D007-取消出金失敗，申請已入帳
    D999-其它出金失敗
    """
    return re_dic
def tran_future_307(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little') > 0:
        #if data[223:224].decode(decode_glogal).strip() in ['N']:
           #return re_dic
        #re_dic.update({'':data[50:51].decode(decode_glogal).strip()})#市場別	Char[1]
        #re_dic.update({'':data[51:54].decode(decode_glogal).strip()})#Web代號	Char[3]
        #re_dic.update({'':data[54:60].decode(decode_glogal).strip()})#網路序號	char[6]
        re_dic.update({'3':data[60:67].decode(decode_glogal).strip()})#總筆數	char[7]
        #re_dic.update({'':data[67:74].decode(decode_glogal).strip()})#目前筆數	char[7]
        #re_dic.update({'cosy':data[74:81].decode(decode_glogal).strip()})#公司別	char[7]
        #re_dic.update({'sett':data[81:88].decode(decode_glogal).strip()})#客戶帳號	char[7]
        re_dic.update({'8':data[88:98].decode(decode_glogal).strip()})#異動日期	char[10]
        re_dic.update({'31':data[98:107].decode(decode_glogal).strip()})#存提單號	char[9]  
        re_dic.update({'11':data[107:114].decode(decode_glogal).strip()})#存款銀行代號	char[7]  
        re_dic.update({'12':data[114:134].decode(decode_glogal).strip()})#存款銀行帳號	char[20] 
        re_dic.update({'14':data[134:141].decode(decode_glogal).strip()})#解款銀行代號	char[7]  
        re_dic.update({'15':data[141:161].decode(decode_glogal).strip()})#解款銀行帳號	char[20] 
        re_dic.update({'16':data[161:171].decode(decode_glogal).strip()})#解款銀行帳戶名稱	Char[10]
        re_dic.update({'4':data[171:172].decode(decode_glogal).strip()})#存提類別	char[1]  
        re_dic.update({'18':data[172:175].decode(decode_glogal).strip()})#幣別	char[3]  
        re_dic.update({'5':data[175:190].decode(decode_glogal).strip()})#原幣金額	char[15]
        re_dic.update({'17':data[190:205].decode(decode_glogal).strip()})#台幣金額	char[15]
        re_dic.update({'27':data[205:208].decode(decode_glogal).strip()})#申請WEBID	char[3]
        re_dic.update({'28':data[208:214].decode(decode_glogal).strip()})#申請網路序號	char[6]
        re_dic.update({'25':data[214:217].decode(decode_glogal).strip()})#取消WEBID	char[3]
        re_dic.update({'26':data[217:223].decode(decode_glogal).strip()})#取消網路序號	char[6]
        re_dic.update({'7':data[223:224].decode(decode_glogal).strip()})#出金是否已出磁片	char[1]
        re_dic.update({'29':""})#單筆結束旗標
        re_dic.update({'30':""})#來源別
        """
        Object {description: "無錯誤", 
                    list: [
                    {3: "2"
                    , 4: "D", 5: "1000000.0000", 6: "TWD", 8: "1061108", 9: "111825001", 11: "8120687", 12: "20680100083899"
                    , 17: "1000000.0000", 18: "TWD", 29: ""},  
                    {4: "D", 5: "1000000.0000", 6: "TWD", 8: "1061108", 9: "111829001", 11: "8120687", 12: "20680100083899"
                    , 17: "1000000.0000", 18: "TWD", 29: ""},  
        """
    return re_dic
def tran_future_307_P(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little') > 0:
        if data[223:224].decode(decode_glogal).strip() in ['Y','C']:
            return re_dic
        #re_dic.update({'':data[50:51].decode(decode_glogal).strip()})#市場別	Char[1]
        #re_dic.update({'':data[51:54].decode(decode_glogal).strip()})#Web代號	Char[3]
        #re_dic.update({'':data[54:60].decode(decode_glogal).strip()})#網路序號	char[6]
        #re_dic.update({'':data[60:67].decode(decode_glogal).strip()})#總筆數	char[7]
        #re_dic.update({'':data[67:74].decode(decode_glogal).strip()})#目前筆數	char[7]
        re_dic.update({'cosy':data[74:81].decode(decode_glogal).strip()})#公司別	char[7]
        re_dic.update({'sett':data[81:88].decode(decode_glogal).strip()})#客戶帳號	char[7]
        re_dic.update({'date':data[88:98].decode(decode_glogal).strip()})#異動日期	char[10]
        re_dic.update({'podt':data[88:98].decode(decode_glogal).strip()})
        #re_dic.update({'':data[98:107].decode(decode_glogal).strip()})#存提單號	char[9]  
        #re_dic.update({'':data[107:114].decode(decode_glogal).strip()})#存款銀行代號	char[7]  
        #re_dic.update({'':data[114:134].decode(decode_glogal).strip()})#存款銀行帳號	char[20] 
        #re_dic.update({'':data[134:141].decode(decode_glogal).strip()})#解款銀行代號	char[7]  
        #re_dic.update({'':data[141:161].decode(decode_glogal).strip()})#解款銀行帳號	char[20] 
        #re_dic.update({'':data[161:171].decode(decode_glogal).strip()})#解款銀行帳戶名稱	Char[10]
        #re_dic.update({'':data[171:172].decode(decode_glogal).strip()})#存提類別	char[1]  
        re_dic.update({'curr':key_exist_in_object(data[172:175].decode(decode_glogal).strip(),curr_response_global)})#幣別	char[3]  
        #re_dic.update({'':data[175:190].decode(decode_glogal).strip()})#原幣金額	char[15]
        #re_dic.update({'':data[190:205].decode(decode_glogal).strip()})#台幣金額	char[15]
        #re_dic.update({'':data[205:208].decode(decode_glogal).strip()})#申請WEBID	char[3]
        #re_dic.update({'':data[208:214].decode(decode_glogal).strip()})#申請網路序號	char[6]
        #re_dic.update({'':data[214:217].decode(decode_glogal).strip()})#取消WEBID	char[3]
        #re_dic.update({'':data[217:223].decode(decode_glogal).strip()})#取消網路序號	char[6]
        #re_dic.update({'':data[223:224].decode(decode_glogal).strip()})#出金是否已出磁片	char[1]
    else:
        re_dic.update({'data':data[26:33].decode(decode_glogal).strip()})#後台結帳中 9990004

    return re_dic
def tran_future_309(data):
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little') > 0:
        #re_dic.update({'':data[50:53].decode(decode_glogal)})#Web代號	Char[3]
        #re_dic.update({'':data[53:59].decode(decode_glogal)})#網路序號	Char[6]
        #re_dic.update({'':data[59:66].decode(decode_glogal)})#資料總筆數	char [7] 
        #re_dic.update({'':data[66:73].decode(decode_glogal)})#目前筆數	char [7] 
        #re_dic.update({'':data[73:80].decode(decode_glogal)})#公司別	Char[7]
        #re_dic.update({'':data[80:87].decode(decode_glogal)})#客戶帳號	Char[7]
        re_dic.update({'statusCode':data[87:90].decode(decode_glogal)})#狀態碼	Char[3]

    return re_dic
def tran_future_310(data):
    #2017/05/19   307+310 
    re_dic = {}
    if int.from_bytes(data[49:50],byteorder='little') > 0:
        #re_dic.update({'':data[50:57].decode(decode_glogal).strip()})#資料總筆數	Char(7)	EX: 0000001
        #re_dic.update({'':data[57:64].decode(decode_glogal).strip()})#目前筆數	Char(7)	EX: 0000002
        re_dic.update({'8':data[64:68].decode(decode_glogal).strip()+"/"+data[68:70].decode(decode_glogal).strip()+"/"+data[70:72].decode(decode_glogal).strip()})#入帳日期	Char(8)	20150101
        #re_dic.update({'cosy':data[72:79].decode(decode_glogal).strip()})#公司別	char[7]	EX: F904000
        #re_dic.update({'':data[79:86].decode(decode_glogal).strip()})#IB	Char[7]	000
        #re_dic.update({'':data[86:93].decode(decode_glogal).strip()})#客戶帳號	char[7]	EX: 1234567
        #re_dic.update({'':data[93:96].decode(decode_glogal).strip()})#客戶組別	Char[3]	分帳資料才有值
        #re_dic.update({'':data[96:102].decode(decode_glogal).strip()})#客戶交易員	char[6]	分帳資料才有值
        re_dic.update({'4':data[102:103].decode(decode_glogal).strip()})#存提類別	char[1]  	C:存 D:提 E:取消
        re_dic.update({'18':data[103:106].decode(decode_glogal).strip()})#幣別	char[3]  	TWD:國內台幣；US$:國內美元； ** :  **:約當台幣;CN$:人民幣
        re_dic.update({'5':data[106:121].decode(decode_glogal).strip()})#原幣金額	char[15]	靠右補空白，含小數
        re_dic.update({'17':data[121:136].decode(decode_glogal).strip()})#台幣金額	char[15]	換算約當台幣金額
        #re_dic.update({'':data[136:142].decode(decode_glogal).strip()})#網路序號	char[6]  	000000
        re_dic.update({'11':data[142:149].decode(decode_glogal).strip()})#存款銀行代號	char[7]  	存入方銀行代號, EX: 0070000
        re_dic.update({'12':data[149:169].decode(decode_glogal).strip()})#存款銀行帳號	char[20] 	存入方銀行帳號, EX:123456789012
        re_dic.update({'14':data[169:176].decode(decode_glogal).strip()})#解款銀行代號	char[7]  	提領方銀行代號, EX: 0070000
        re_dic.update({'15':data[176:196].decode(decode_glogal).strip()})#解款銀行帳號	char[20] 	提領方銀行帳號, EX:123456789012
        re_dic.update({'16':data[196:206].decode(decode_glogal).strip()})#解款銀行帳戶名稱	Char[10]	EX: 0130000
        re_dic.update({'31':data[206:215].decode(decode_glogal).strip()})#存提單號	Char[9]	存提單號:異動時間(左靠)+流水號(右靠右靠) HHMMSS+XXX
        re_dic.update({'30':data[215:216].decode(decode_glogal).strip()})#來源別	Char[1]	網路:I  現場:W
        re_dic.update({'7':data[216:217].decode(decode_glogal).strip()})#出金是否已出磁片	char[1]	Y:是 N:否 C:取消 
        re_dic.update({'29':""})#單筆結束旗標
    else:
        re_dic.update({'data':data[26:33].decode(decode_glogal).strip()})#後台結帳中 9990004
    return re_dic
# ==== urlopen ====
def bobo_urlopen(url_):
    req = Request(url_)
    try:
        response = urlopen(req)
    except HTTPError as e:
        write_log_txt('Error code: ', e.code)
    except URLError as e:
        write_log_txt('Reason: ', e.reason)
    #data = response.read()
    return response
# ==== XML FUNC ====
def write_response_xml(dic_all_in):
    TARoot = ET.Element('TARoot')
    TARoot.attrib = key_exist_in_object('dic_TARoot',dic_all_in)
    TAUser = ET.SubElement(TARoot,'TAUser')
    TAUser.attrib = key_exist_in_object('dic_TAUser',dic_all_in)
    TAStatus = ET.SubElement(TARoot,'TAStatus')
    TAStatus.attrib = key_exist_in_object('dic_TAStatus',dic_all_in)
    if key_exist_in_object('list_GetMarkPass',dic_all_in) != '':#000 login
        TAPassport = ET.SubElement(TARoot,'TAPassport')
        CACMACUS = ET.SubElement(TAPassport,'CACMACUS')
        CACMACUS.attrib = key_exist_in_object('dic_CACMACUS',dic_all_in)
        for item in key_exist_in_object('stock_account_list',dic_all_in['list_GetMarkPass']):
            SBCMACUS = ET.SubElement(CACMACUS,'SBCMACUS')
            SBCMACUS.attrib = item
            
        for item in key_exist_in_object('futures_account_list',dic_all_in['list_GetMarkPass']):
            OBCMACUS = ET.SubElement(CACMACUS,'OBCMACUS')
            OBCMACUS.attrib = item

        #for item in key_exist_in_object('HK_stock_account_list',dic_all_in['list_GetMarkPass']):
            #HKSBCMACUS = ET.SubElement(CACMACUS,'HKSBCMACUS')
            #HKSBCMACUS.attrib = item
    TAFinish = ET.SubElement(TARoot,'TAFinish')
    root = ET.ElementTree(TARoot)
    #write_log_txt(ET.tostring(TARoot))
    return ET.tostring(TARoot)
def symb_ch_name_search(symb_):
    global comm02_contract_data
    if len(comm02_contract_data) == 0:
        f = open("C:\\Python34\\COMM02.txt", 'r',encoding=decode_glogal)
        comm02_contract_data = f.readlines()
    symb_ch_name = ""
    symb_short_name = ""
    for item in comm02_contract_data:
        try:
            if str(symb_).strip()[0:3] == item[6:16].strip():
                symb_ch_name = item.encode(decode_glogal)[20:62].decode(decode_glogal).strip()#完整中文名稱
                symb_short_name = item.encode(decode_glogal)[106:128].decode(decode_glogal).strip()#商品中文簡稱
        except:
            write_log_txt('symb_ch_name_search error at '+ str(symb_).strip()[0:3])
            pass
    return symb_short_name
def get_all_future_contract_data(Exchange_,type_,TradeID_list,ClassID_list,StkID_list):
    global comm02_contract_data
    basic_ClassID = 10000*int(type_)
    list_all_future_contract_data = []
    if len(comm02_contract_data) == 0:
        f = open("C:\\Python34\\COMM02.txt", 'r',encoding=decode_glogal)
        comm02_contract_data = f.readlines()
    for item in comm02_contract_data:
        if str(Exchange_).strip() == item[0:6].strip() and str(type_).strip() == item[16:17].strip():#交易所, 期/選
            symb = item[6:16].strip()#商品代碼
            if symb[:2] in ['MX','TX'] or symb[2] in ['F','O']:
                symb_short_name = item.encode(decode_glogal)[106:128].decode(decode_glogal).strip()#商品中文簡稱
                list_all_future_contract_data.append({"TradeID":list_to_dict(TradeID_list).get(symb.lower(),'FI'+symb),
                                                      "Name":symb_short_name,
                                                      "QuoteID":symb,
                                                      "ClassID":list_to_dict(ClassID_list).get(symb.lower(),basic_ClassID),
                                                      "StkID":list_to_dict(StkID_list).get(symb.lower(),'T1')})
                basic_ClassID = basic_ClassID+1

    return list_all_future_contract_data
def list_to_dict(list_of_key_value):
    NameMapping = dict()
    for item in list_of_key_value:
        NameMapping[item[0]] = item[1]
    return NameMapping
#region ==== xml tag FUNC start ====
def make_NGPMAERRS(recv_data_dict_):
    dic_NGPMAERRS = {}
    dic_NGPMAERRS.update({'prio':'0'})#未知
    dic_NGPMAERRS.update({'coer':'0'})#未知
    dic_NGPMAERRS.update({'type':'0'})#未知
    dic_NGPMAERRS.update({'tacontainer':'1'})#既然有錯誤的話,NGPMAERR就只會有一筆
    return dic_NGPMAERRS
def make_NGPMAERR(recv_data_dict_):
    dic_NGPMAERR = {}
    dic_NGPMAERR.update({'leve':'5'})
    dic_NGPMAERR.update({'code':key_exist_in_object('code',recv_data_dict_)})
    dic_NGPMAERR.update({'cause':key_exist_in_object('cause',recv_data_dict_)})
    dic_NGPMAERR.update({'action':key_exist_in_object('cause',recv_data_dict_)})
    return dic_NGPMAERR
def make_TARoot(recv_data_dict_):
    dic_TARoot = {}
    dic_TARoot.update({'type':'2'})
    dic_TARoot.update({'now':str(int(str(datetime.datetime.now())[0:4])-1911)+"/"+str(datetime.datetime.now())[5:7]+"/"+str(datetime.datetime.now())[8:10]})
    return dic_TARoot
def make_TAUser(recv_data_dict_):
    dic_TAUser = {}
    dic_TAUser.update({'idno':key_exist_in_object('idno',recv_data_dict_)})
    dic_TAUser.update({'name':""})
    return dic_TAUser
def make_CACPARTYS(recv_data_dict_):
    dic_CACPARTYS = {}
    dic_CACPARTYS.update({"count":"1"})
    return dic_CACPARTYS
def make_CACPARTY(recv_data_dict_):
    dic_CACPARTY = {}
    dic_CACPARTY.update({"type":"2"})
    dic_CACPARTY.update({"comp":key_exist_in_object('comp',recv_data_dict_)})
    dic_CACPARTY.update({'cosy':key_exist_in_object('cosy',recv_data_dict_)})
    dic_CACPARTY.update({'cona':'中菲期貨'})
    dic_CACPARTY.update({"cuno":key_exist_in_object('sett',recv_data_dict_)})
    dic_CACPARTY.update({"name":key_exist_in_object('cuna',recv_data_dict_)})
    dic_CACPARTY.update({"idno":key_exist_in_object('idno',recv_data_dict_)})
    dic_CACPARTY.update({"ctno":"------------------------65---10"})
    return dic_CACPARTY
def make_TAStatus(recv_data_dict_):
    dic_TAStatus = {}
    dic_TAStatus.update({'description':key_exist_in_object('description',recv_data_dict_)})
    dic_TAStatus.update({'code':key_exist_in_object('code',recv_data_dict_)})
    dic_TAStatus.update({'count':'0'})
    return dic_TAStatus
def make_OBFORDERS(recv_data_dict_):#委託回補
    dic_OBFORDERS = {}
    dic_OBFORDERS.update({'perm':'-----wrb'})
    dic_OBFORDERS.update({'tacontainer':key_exist_in_object('tacontainer',recv_data_dict_)})
    dic_OBFORDERS.update({'unlimited':'0'})
    return dic_OBFORDERS
def make_OBFEXECUS(recv_data_dict_):#成交回補
    dic_OBFEXECUS = {}
    dic_OBFEXECUS.update({'perm':'-----wrb'})
    dic_OBFEXECUS.update({'tacontainer':key_exist_in_object('tacontainer',recv_data_dict_)})
    dic_OBFEXECUS.update({'unlimited':'0'})
    return dic_OBFEXECUS
def make_TABody():#委託成交回補無資料時
    dict_TABody = {}
    dict_TABody.update({'perm':'-----wrb'})
    return dict_TABody
def make_OBBOFINVS():#庫存(兩隻腳的head)
    dict_OBBOFINVS = {}
    dict_OBBOFINVS.update({'tacontainer':'2'})
    return dict_OBBOFINVS
def make_OBBOFINV():#庫存(兩隻腳的內容)
    dict_OBBOFINV = {}
    return dict_OBBOFINV
def make_CACMACUS(recv_data_dict_):
    dict_CACMACUS = {}
    dict_CACMACUS.update({'idno':key_exist_in_object('idno',recv_data_dict_)})
    dict_CACMACUS.update({'name':''})
    return dict_CACMACUS
def make_CPAPERMIS():
    dict_CPAPERMIS = {}
    dict_CPAPERMIS.update({'count':'1'})
    return dict_CPAPERMIS
def make_CPAPERMI():
    dict_CPAPERMI = {}
    dict_CPAPERMI.update({'inte':'1.1.1.1'})
    dict_CPAPERMI.update({'oper':'11'})
    dict_CPAPERMI.update({'syna':'客戶密碼管理作業'})
    dict_CPAPERMI.update({'perm':'-----wrb'})
    return dict_CPAPERMI
def make_CPROFILES():
    dict_CPROFILES = {}
    dict_CPROFILES.update({'count':'1'})
    return dict_CPROFILES
def make_CPROFILE():
    dict_CPROFILE = {}
    dict_CPROFILE.update({'pfid':'1'})
    dict_CPROFILE.update({'pfvl':'0'})
    return dict_CPROFILE
#306
def make_OBFORDURS(recv_data_dict_):
    dict_OBFORDURS = {}
    dict_OBFORDURS.update({'tacontainer':key_exist_in_object('tacontainer',recv_data_dict_)})
    return dict_OBFORDURS
#307
def make_CAFJOURNS(recv_data_dict_):
    dict_CAFJOURNS = {}
    dict_CAFJOURNS.update({'perm':'-----wrb'})
    dict_CAFJOURNS.update({'tacontainer':key_exist_in_object('tacontainer',recv_data_dict_)})
    return dict_CAFJOURNS
#001
def make_CACLIAISS():
    dict_CACLIAISS = {}
    return dict_CACLIAISS
def make_CACLIAIS():
    dict_CACLIAIS = {}
    dict_CACLIAIS.update({'lino':'0'})
    dict_CACLIAIS.update({'liad':'桃園市龜山區大崗里21鄰大湖路406號'})
    dict_CACLIAIS.update({'lizi':'333'})
    dict_CACLIAIS.update({'lite':'033364560'})
    dict_CACLIAIS.update({'lifa':''})
    dict_CACLIAIS.update({'limm':''})
    return dict_CACLIAIS
def make_CACCONNES():
    dict_CACCONNES = {}
    return dict_CACCONNES
def make_CACCONNE():
    dict_CACCONNE = {}
    dict_CACCONNE.update({'cono':'6'})
    dict_CACCONNE.update({'coid':'6460'})
    dict_CACCONNE.update({'cona':''})
    dict_CACCONNE.update({'core':''})
    dict_CACCONNE.update({'coht':'6460'})
    dict_CACCONNE.update({'coot':''})
    dict_CACCONNE.update({'comt':''})
    dict_CACCONNE.update({'comm':''})
    return dict_CACCONNE
def make_CACCONTRS():
    dict_CACCONTRS = {}
    return dict_CACCONTRS
def make_CACCONTR(recv_data_dict_):
    dict_CACCONTR = {}
    #<CACCONTR ctno='0' ctco='' ctii='105/05/03' ctmo='105/06/08' ctcl='' ctst='0' ctlc='' ctsc='' ctmm=''/>
    dict_CACCONTR.update({'ctno':'0'})
    dict_CACCONTR.update({'ctco':''})
    dict_CACCONTR.update({'ctii':'105/05/03'})
    dict_CACCONTR.update({'ctmo':key_exist_in_object('date',recv_data_dict_)})
    dict_CACCONTR.update({'ctcl':''})
    dict_CACCONTR.update({'ctst':'0'})
    dict_CACCONTR.update({'ctlc':''})
    dict_CACCONTR.update({'ctsc':''})
    dict_CACCONTR.update({'ctmm':''})
    return dict_CACCONTR
#endregion ==== xml tag FUNC end ====
if __name__ == '__main__':
    """
    global comm02_contract_data
    #global comm02_contract_future_data
    #global comm02_contract_option_data
    try:
        f = open("D:\\COMM02.txt", 'r',encoding=decode_glogal)
        comm02_contract_data = f.readlines()
        
        for item in f.readlines():#每日global儲存
            comm02_contract_future_data.append()
            comm02_contract_option_data.append()
    except:
        write_log_txt('COMM02 readlines error ')
    """

#更新紀錄 20180307 16:05