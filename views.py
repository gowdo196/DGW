#-*- coding: utf8 -*-
from django.http.response import HttpResponse
#from django.contrib.sessions.models import Session
import sys
import os
import json
import requests
import datetime
import psycopg2
import configparser
from requests import Request#, Session
from urllib import parse
sys.path.append('C:\\Python34\\mysite\\DGW')
import dgw_main
import ProdConvert
#20171121 Dcn_GateWay_main setup
xml_encode_charset = "utf8"
logpath = "C:\\Python34\\mysite\\DGW\\"
logtxt_filename = "dgw_log.txt"
global TAMarket_value
global TAShare_value
TAMarket_value = ""
TAShare_value = ""
dazu_response_log_path = "C:\\Python34\\mysite\\DGW\\dazu_response_log\\dazu_response_"
#dazu_func_list_of_ignore = ["IsTradeDay","IsTradeTime","NextTradeDay","NextTradeDayddddd","GetXBIMAIns","mfcISAPICommand=GetCPCPkCer","GetCPCPkCer"]
ajax_url_keyword = ["/redirect_dgw/Servlet?&url=","/redirect_dgw/BAServlet?&url=","/redirect_dgw/Servlet?","/redirect_dgw/BAServlet?"]
Test_Server_view_mode = True
def write_dazu_response_log_txt(object,path_):
    #logList = read_log_txt()
    f = open(path_,"a")

    f.write("\n"+str(object))
    f.close()
def response_mode_switch(request,dic_all_in,response_mode_):
    p = default(request)
    try:
        if response_mode_ == 'json':
            response_json = json.dumps(dic_all_in, ensure_ascii=False, sort_keys=True, indent=4)
            p = HttpResponse(response_json, content_type="application/json; charset="+xml_encode_charset)
        else:
            if len(dgw_main.key_exist_in_object('dic_TARoot',dic_all_in)) == 0:
                dic_all_in.update({'dic_TARoot':dgw_main.make_TARoot(dic_all_in)})
            if len(dgw_main.key_exist_in_object('dic_TAUser',dic_all_in)) == 0:
                dic_all_in.update({'dic_TAUser':dgw_main.make_TAUser(dic_all_in)})
            if len(dgw_main.key_exist_in_object('dic_TAStatus',dic_all_in)) == 0:
                dic_all_in.update({'dic_TAStatus':dgw_main.make_TAStatus(dic_all_in)})
            response_xml = dgw_main.write_response_xml(dic_all_in)
            p = HttpResponse(response_xml.decode(xml_encode_charset),content_type="text/xml; charset=" + xml_encode_charset)
            p['apexsessionid'] = dgw_main.key_exist_in_object('sign_str_result',dic_all_in)
    except:
        write_log_txt('response_mode_switch error response_mode_= ' + response_mode_ + ", dic_all_in ="+str(dic_all_in))
        pass
    return p
def redirect_dgw(request):
    global TAMarket_value
    global TAShare_value
    #request.get_host()#Example: "127.0.0.1:8000"
    #最初收到的完整URL(去掉GateWay關鍵字)
    og_str = requests.utils.unquote(requests.utils.unquote(request.get_full_path()))

    write_log_txt('og_str = ' + og_str)
    response_mode = 'xml'
    if og_str.find('BAServlet') > 0:
        response_mode = 'json'
    for item in ajax_url_keyword:
        og_str = og_str.replace(item,'')
    if og_str.find('redirect_dgw') > 0:
        return HttpResponse("<TARoot><default>預設回應</default><default2>有時候會放些測試資料呵呵噠</default2></TARoot>",content_type="text/xml; charset=" + xml_encode_charset)
    #萬用key
    cookies=dict(TAMarket=TAMarket_value,TAShare=TAShare_value,TAWork='CB6JiBjCI/ZWRQV7y2ChXlz8fWV7T7/l8EVb02fVJGC5sKEg0O473bac7VavPl4XUk7tCsoM0ysalHSIwyc3FbC6FP+SpbAmkpbuA4AcEDkzp7/ouuGyBKXlVqk9bpA/aMFSNAw7yq3+JnrS9AIWTw==')

    header_dic = {}
    header_dic.update({"Expect":"100"})
    header_dic.update({"Host":"ap-test.dcn.com.tw"})
    header_dic.update({"Content-Type":""})
    header_dic.update({"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"})
    header_dic.update({"Connection": "keep-alive"})

    switch_str = og_str.split('?&url=')[0]
    if og_str.split('?&url=')[0] == og_str:
        xml_list = og_str   #大洲
    else:
        xml_list = og_str.split('?&url=')[1]
    list_of_post = ""
    #GET POST 統一結果方便後續處理
    if request.method == 'GET':
        list_of_post = xml_list
    elif request.method == 'POST':
        list_of_post = str(request.body.decode('big5'))
    else:
        return default(request)
    list_of_post_ = post_to_url(list_of_post)#GET POST分別處理完之後的結果

    write_log_txt('list_of_post_ = '+list_of_post_)
    dic_all_in = {}#xml body 共用一個dict
    dic_xml_head_dict = {}#xml head 共用一個dict
    dic_xml_head_dict.update({'switch_str':switch_str})
    dic_xml_head_dict.update({'xml_list_0':xml_list.split('&')[0]})
    dic_xml_head_dict.update(build_xml_head(list_of_post_))
    
    sid = ""
    ApexDB_cursor_ = build_ApexDB_cursor_()
    if Test_Server_view_mode:
        pass
    else:
        try:
            #sid = dgw_main.key_exist_in_object('sid',dic_xml_head_dict)
            sid = request.META.get('HTTP_APEXSESSIONID', '')
            if len(sid) == 0 and xml_list.split('&')[0] == "login":#沒有sid不一定表示是登入...
                pass
            elif len(sid) > 0:
                sqlcmd = "SELECT scontent,expire_time from public.tb_gateway_session_info where sid = '"+sid+"'"
                ApexDB_cursor_.execute(sqlcmd)
                session_expire_datetime = ApexDB_cursor_.fetchall()[0][1]
                if session_expire_datetime > str(datetime.datetime.now()):
                    sign_check_result = dgw_main.sha_sign(request.META.get('REMOTE_ADDR', 'REMOTE_ADDR_miss')+'_'+request.META.get('HTTP_USER_AGENT', 'HTTP_USER_AGENT_miss')+'_'+session_expire_datetime+'_'+get_ini_str("DCN_GW", "token"))#固定值可放config
                    if sign_check_result == sid:
                        pass
                    else:
                        #盜用來源
                        dic_all_in.update({'code':'-1100'})
                        dic_all_in.update({'description':'盜用是要喀擦的噢'})
                        return response_mode_switch(request,dic_all_in,response_mode)
                else:
                    #token過期,重新登入
                    dic_all_in.update({'code':'-1200'})
                    dic_all_in.update({'description':'token已過期請重新登入'})
                    return response_mode_switch(request,dic_all_in,response_mode)
            else:
                dic_all_in.update({'code':'-1000'})
                dic_all_in.update({'description':'您無該帳號權限'})
                return response_mode_switch(request,dic_all_in,response_mode)
        except:
            write_log_txt('==== META get apex_session_id error ===='+str(sys.exc_info()))
            #來源會拿不到
            dic_all_in.update({'code':'-1000'})
            dic_all_in.update({'description':'META get apex_session_id error 您無該帳號權限'})
            return response_mode_switch(request,dic_all_in,response_mode)

    if Session_search(sid,dgw_main.key_exist_in_object('sett',dic_xml_head_dict),ApexDB_cursor_) or len(dgw_main.key_exist_in_object('sett',dic_xml_head_dict)) == 0:
        try:
            write_log_txt('==== before '+xml_list.split('&')[0]+' send ==== response_mode ===='+response_mode)
            if xml_list.split('&')[0] == "login":#000 登入
                #dic_xml_head_dict.update({'idno':dgw_main.key_exist_in_object('idno',dic_xml_head_dict)})
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'000')#回傳 binary data
                #有可能有不認識的id, tran_future_000會幫忙建立DB不存在的身分證和帳號
                dic_recv = {}
                dic_recv = dgw_main.tran_future_000(recv_data,dgw_main.key_exist_in_object('idno',dic_xml_head_dict))#從中菲回來的電文處理 000後,轉成dict(1次)
                write_log_txt('login dic_recv size='+str(len(dic_recv)))
                #完全無資料的狀況
                if len(dgw_main.key_exist_in_object('errorcode',dic_recv))>0:
                    dic_xml_head_dict.update({'description':dgw_main.key_exist_in_object('error_msg',dic_recv)})
                    dic_xml_head_dict.update({'code':dgw_main.key_exist_in_object('errorcode',dic_recv)})
                else:
                    dic_all_in.update({'list_GetMarkPass':dic_recv})
                    dic_xml_head_dict.update({'description':'無錯誤'})
                    dic_xml_head_dict.update({'code':'0'})
                    #取出明文製作token值
                    x = datetime.datetime.now()
                    y = datetime.timedelta(hours=int(get_ini_str("DCN_GW", "expire_hour")))
                    sign_str_result = dgw_main.sha_sign(request.META.get('REMOTE_ADDR', 'REMOTE_ADDR_miss')+'_'+request.META.get('HTTP_USER_AGENT', 'HTTP_USER_AGENT_miss')+'_'+str(x+y)+'_'+get_ini_str("DCN_GW", "token"))
                    #write_log_txt("sign_str_result="+sign_str_result)
                    dic_all_in.update({'sign_str_result':sign_str_result})

                dic_all_in.update({'dic_TARoot':dgw_main.make_TARoot(dic_xml_head_dict)})
                dic_all_in.update({'dic_TAUser':dgw_main.make_TAUser(dic_xml_head_dict)})
                dic_all_in.update({'dic_TAStatus':dgw_main.make_TAStatus(dic_xml_head_dict)})
                dic_all_in.update({'dic_CACMACUS':dgw_main.make_CACMACUS(dic_xml_head_dict)})
                #write_log_txt('login dic_all_in=')
                #write_log_txt(dic_all_in)
                #request.session['lucky'] = dgw_main.key_exist_in_object('idno',dic_xml_head_dict)#session idno login
                #request.session['LoginResp'] = dic_all_in#session LoginResp
                if len(dgw_main.key_exist_in_object('sign_str_result',dic_all_in))>0:
                    sqlcmd = "insert into public.tb_gateway_session_info (idno,sid,scontent,expire_time) VALUES \
                    ('"+dgw_main.key_exist_in_object('idno',dic_xml_head_dict)+"','"+sign_str_result+"','"+str(dic_all_in).replace('\'','\"')+"','"+str(x+y)+"');"
                    ApexDB_cursor_.execute(sqlcmd)
            elif xml_list.split('&')[0] in ["url=GetLoginResp2","GetLoginResp","GetLoginResp2"]:#001_P 查詢客戶資料
                #session_lucky = ""
                session_LoginResp = {}
                try:
                    sqlcmd = "SELECT scontent,expire_time from public.tb_gateway_session_info where sid = '"+sid+"'"
                    ApexDB_cursor_.execute(sqlcmd)
                    session_LoginResp = ApexDB_cursor_.fetchall()[0][0]
                    session_expire_datetime = ApexDB_cursor_.fetchall()[0][1]
                    #session_lucky = request.session['lucky']
                    #session_LoginResp = request.session['LoginResp']# 20180122 API客戶權限控管   拿list_GetMarkPass出來看 非群組內不給用
                except:
                    pass

                if len(sid)>0 and len(session_LoginResp) > 0:#session idno check exist
                    #write_log_txt("session_LoginResp=")
                    #write_log_txt(session_LoginResp)
                    dic_all_in = session_LoginResp
                    dic_xml_head_dict.update({'description':'無錯誤'})
                    dic_xml_head_dict.update({'code':'0'})
                    #sid = request.COOKIES['sessionid']
                else:
                    #write_log_txt("session_lucky="+str(sid))
                    #dic_xml_head_dict.update({'sid':''})
                    dic_xml_head_dict.update({'description':'無用戶個人身份資料,請按正常程序登入系統'})
                    dic_xml_head_dict.update({'code':'-1000'})

                    dic_all_in.update({'dic_TARoot':dgw_main.make_TARoot(dic_xml_head_dict)})
                    dic_all_in.update({'dic_TAUser':dgw_main.make_TAUser(dic_xml_head_dict)})
                    dic_all_in.update({'dic_TAStatus':dgw_main.make_TAStatus(dic_xml_head_dict)})
                    dic_all_in.update({'dic_CACMACUS':dgw_main.make_CACMACUS(dic_xml_head_dict)})
            elif xml_list.split('&')[0] in ["url=changeUserPassword","changeUserPassword","unlockPassword"]:#002 變更密碼 變更出金密碼
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'002')
                dic_recv = dgw_main.tran_future_002(recv_data)
                dic_all_in.update({'description':dgw_main.key_exist_in_object('error_msg',dic_recv)})
                dic_all_in.update({'code':dgw_main.key_exist_in_object('errorcode',dic_recv)})
            elif xml_list.split('&')[0] in ["url=getUserInfo","getUserInfo"]:#004 出入金帳號查詢
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'004')
                #紀錄socket結束後收到的list
                write_log_txt('004 recv_data size=' + str(len(recv_data)))
                list_withdrawAccountList = []
                for item in recv_data:
                    dic_recv = {}
                    dic_recv = dgw_main.tran_future_004(item)#從中菲回來的電文處理004後,轉成dict(N次)
                    if len(dic_recv) > 0:
                        list_withdrawAccountList.append(dic_recv)

                #==== 無 ====
                if len(list_withdrawAccountList) == 0:
                    dic_all_in.update({'description':'查無任何資料,請重新輸入查詢條件'})
                dic_all_in.update({'code':'0'})
                dic_all_in.update({'withdrawAccountList':list_withdrawAccountList})
            elif xml_list.split('&')[0] in ["url=checkUserPassword","checkUserPassword"]:#000_P 出金密碼檢核
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'000_P')
                dic_recv = dgw_main.tran_future_002(recv_data)
                dic_all_in.update({'description':dgw_main.key_exist_in_object('error_msg',dic_recv)})
                dic_all_in.update({'code':dgw_main.key_exist_in_object('errorcode',dic_recv)})
            elif xml_list.split('&')[0] in ["url=reportDataT20","reportDataT20"]:#100 期貨下單
                if str(dic_xml_head_dict['execType']) == '0':#type
                    recv_data = dgw_main.bobo_main_socket(list_of_post_,'100')
                    dic_OBFORDER = dgw_main.tran_future_100(recv_data)
                elif str(dic_xml_head_dict['execType']) in ['4','5','M']:#4:刪單5:改量M:改價
                    recv_data = dgw_main.bobo_main_socket(list_of_post_,'101')
                    dic_OBFORDER = dgw_main.tran_future_101(recv_data)
                write_log_txt('order future type =' + dic_xml_head_dict['execType'] + ' dic_OBFORDER=')
                write_log_txt(dic_OBFORDER)

                if dgw_main.key_exist_in_object('code',dic_OBFORDER) == '' and dgw_main.key_exist_in_object('cause',dic_OBFORDER) == '':
                    dic_all_in.update({'code':'0'})
                    dic_all_in.update({"description":"委託成功"})
                else:#製作出NGPMAERRS, NGPMAERR 一旦有這兩個dict則xml會直接產錯誤訊息版本
                    dic_all_in.update({'code':dgw_main.key_exist_in_object('code',dic_OBFORDER)})#orderserver僅吃Int數字,此欄非0即可,真正的錯誤碼放置於cause
                    dic_all_in.update({'description':dgw_main.key_exist_in_object('cause',dic_OBFORDER)})
            elif xml_list.split('&')[0] in ["url=reportDataB20","reportDataB20"]:#200 期貨庫存
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'200')#200 單式回傳
                #紀錄socket結束後收到的list
                write_log_txt('200 recv_data size=' + str(len(recv_data)))
                list_OBBPOSIT = []
                for item in recv_data:
                    dic_recv = {}
                    dic_recv = dgw_main.tran_future_200(item)#從中菲回來的電文處理200後,轉成dict(N次)
                    if len(dic_recv) > 0:
                        list_OBBPOSIT.append(dic_recv)
                #==== 無 ====
                if len(list_OBBPOSIT) == 0:
                    dic_all_in.update({'list':[]})
                    dic_all_in.update({'code':'0'})
                    dic_all_in.update({'description':'查無任何資料,請重新輸入查詢條件'})
                #==== N筆 ====
                else:
                    dic_all_in.update({'list':list_OBBPOSIT})
                    dic_all_in.update({'code':'0'})
            elif xml_list.split('&')[0] in ["url=reportDataB22","reportDataB22"]:#203+204 期貨庫存
                item_list = list_of_post_.split('&')
                item_dic = {}
                for item in item_list:
                    if len(item.split('='))==2:
                        item_dic.update({item.split('=')[0]:item.split('=')[1]})
                    elif len(item.split('='))==1:
                        item_dic.update({item.split('=')[0]:item.split('=')[0]})
                    else:
                        item_dic.update({item.split('=')[0]:''})

                recv_data = dgw_main.bobo_main_socket(list_of_post_,'203')#203
                #紀錄socket結束後收到的list
                write_log_txt('reportDataB22 recv_data 203 size=' + str(len(recv_data)))
                list_OBBPOSIT = []
                for item in recv_data:
                    dic_recv = {}
                    dic_recv = dgw_main.tran_future_203(item)#從中菲回來的電文處理203後,轉成dict(N次)
                    if len(dic_recv) > 0 and int(dic_recv['7']) >= int(dgw_main.yyymmdd_mutual_yyyymmdd(item_dic['date'],'')) and int(dic_recv['7']) <= int(dgw_main.yyymmdd_mutual_yyyymmdd(item_dic['date1'],'')):
                        list_OBBPOSIT.append(dic_recv)
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'204')#204 
                #紀錄socket結束後收到的list
                write_log_txt('reportDataB22 recv_data 204 size=' + str(len(recv_data)))
                for item in recv_data:
                    dic_recv = {}
                    dic_recv = dgw_main.tran_future_204(item)#從中菲回來的電文處理204後,轉成dict(N次)
                    if len(dic_recv) > 0:
                        list_OBBPOSIT.append(dic_recv)
                #==== 無 ====
                if len(list_OBBPOSIT) == 0:
                    dic_all_in.update({'list':[]})
                    dic_all_in.update({'code':'0'})
                    dic_all_in.update({'description':'查無任何資料,請重新輸入查詢條件'})
                #==== 複式單N筆 ====
                else:
                    dic_all_in.update({'list':list_OBBPOSIT})
                    dic_all_in.update({'code':'0'})
            elif xml_list.split('&')[0] in ["url=reportDataB21","reportDataB21"]:#207 權益數
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'207')#回傳list of binary data
                #紀錄socket結束後收到的list size
                write_log_txt('reportDataB21 recv_data len=' + str(len(recv_data)))
                list_CAFMAFUN = []
                for item in recv_data:
                    dic_recv = {}
                    dic_recv = dgw_main.tran_future_207(item)#處理207後,轉成dict(N次)
                    list_CAFMAFUN.append(dic_recv)
                #write_log_txt(list_CAFMAFUN)
                #==== 無 ====
                if len(list_CAFMAFUN) == 0:
                    dic_all_in.update({'description':'查無任何資料,請重新輸入查詢條件'})
                dic_all_in.update({'list':list_CAFMAFUN})
                dic_all_in.update({'code':'0'})
            elif xml_list.split('&')[0] in ["url=reportDataT21","reportDataT21"]:#208+211 期貨委託回補
                list_OBFORDER = []
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'211')#回傳list of binary data
                #紀錄socket結束後收到的list size
                write_log_txt('reportDataT21 recv_data 211 len=' + str(len(recv_data)))
                for item in recv_data:
                    dic_recv = {}
                    dic_recv = dgw_main.tran_future_211(item)#從中菲回來的電文處理208後,轉成dict(N次)
                    if len(dic_recv) > 0:
                        list_OBFORDER.append(dic_recv)
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'208')#回傳list of binary data
                #紀錄socket結束後收到的list size
                write_log_txt('reportDataT21 recv_data 208 len=' + str(len(recv_data)))
                for item in recv_data:
                    dic_recv = {}
                    dic_recv = dgw_main.tran_future_208(item)#從中菲回來的電文處理211後,轉成dict(N次)
                    if len(dic_recv) > 0:
                        list_OBFORDER.append(dic_recv)
                #==== 無委託回補 ====
                if len(list_OBFORDER) < 1:
                    dic_all_in.update({'list':[]})
                    dic_all_in.update({'code':'0'})
                    dic_all_in.update({'description':'查無任何資料,請重新輸入查詢條件'})
                #==== 後台結帳中 ====
                elif dgw_main.key_exist_in_object('data',list_OBFORDER[0]) == '9990004':
                    dic_all_in.update({'code':'9990004'})
                    dic_all_in.update({'description':'後台結帳中'})
                #==== 委託回補N筆 ====
                else:
                    dic_all_in.update({'list':list_OBFORDER})
                    dic_all_in.update({'code':'0'})
            elif xml_list.split('&')[0] in ["url=reportDataT22","reportDataT22"]:#209+212 期貨成交回補
                list_OBFORDER = []
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'212')#回傳list of binary data
                #紀錄socket結束後收到的list size
                write_log_txt('reportDataT22 recv_data 212 size='+str(len(recv_data)))
                for item in recv_data:
                    dic_recv = {}
                    dic_recv = dgw_main.tran_future_212(item)#從中菲回來的電文處理209後,轉成dict(N次)
                    list_OBFORDER.append(dic_recv)
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'209')#回傳list of binary data
                #紀錄socket結束後收到的list size
                write_log_txt('reportDataT22 recv_data 209 size='+str(len(recv_data)))
                for item in recv_data:
                    dic_recv = {}
                    dic_recv = dgw_main.tran_future_209(item)#從中菲回來的電文處理209後,轉成dict(N次)
                    list_OBFORDER.append(dic_recv)
                #==== 無成交回補 ====
                if len(list_OBFORDER) == 0:
                    dic_all_in.update({'code':'0'})
                    dic_all_in.update({'description':'查無任何資料,請重新輸入查詢條件'})
                #==== 成交回補N筆 ====
                else:
                    dic_all_in.update({'list':list_OBFORDER})
                    dic_all_in.update({'code':'0'})
            elif xml_list.split('&')[0] in ["url=reportDataB50","reportDataB50"]:#306 出金申請
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'306')
                #紀錄socket結束後收到的list size
                write_log_txt('reportDataB50 recv_data size='+str(len(recv_data)))
                dic_all_in = dgw_main.tran_future_306(recv_data)#回傳list of binary data
            elif xml_list.split('&')[0] in ["url=reportDataB51","reportDataB51"]:#307 出入金歷史查詢
                list_CAFJourn = []
                item_list = list_of_post_.split('&')
                item_dic = {}
                for item in item_list:
                    if len(item.split('='))==2:
                        item_dic.update({item.split('=')[0]:item.split('=')[1]})
                    elif len(item.split('='))==1:
                        item_dic.update({item.split('=')[0]:item.split('=')[0]})
                    else:
                        item_dic.update({item.split('=')[0]:''})
                
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'307')
                write_log_txt(' 307 recv_data size='+str(len(recv_data)))#多筆

                for item in recv_data:
                    dic_recv = {}
                    dic_recv = dgw_main.tran_future_307(item)#從中菲回來的電文處理307後,轉成dict(N次)
                    if len(dic_recv) > 0 and int(dic_recv['8'].replace('/','')) >= int(dgw_main.yyymmdd_mutual_yyyymmdd(item_dic['date'],'')) and int(dic_recv['8'].replace('/','')) <= int(dgw_main.yyymmdd_mutual_yyyymmdd(item_dic['date1'],'')):
                        list_CAFJourn.append(dic_recv)

                recv_data = dgw_main.bobo_main_socket(list_of_post_,'310')
                write_log_txt(' 310 recv_data size='+str(len(recv_data)))#多筆
                for item in recv_data:
                    dic_recv = {}
                    dic_recv = dgw_main.tran_future_310(item)#從中菲回來的電文處理307後,轉成dict(N次)
                    if len(dic_recv) > 0:
                        list_CAFJourn.append(dic_recv)

                if len(list_CAFJourn) == 0:
                    dic_all_in.update({'list':[]})
                    dic_all_in.update({'code':'0'})
                    dic_all_in.update({'description':'查無任何資料,請重新輸入查詢條件'})
                #==== 後台結帳中 ====
                elif dgw_main.key_exist_in_object('data',list_CAFJourn[0]) == '9990004':
                    dic_all_in.update({'list':[]})
                    dic_all_in.update({'code':'9990004'})
                    dic_all_in.update({'description':'後台結帳中'})
                #==== N筆 ====
                else:
                    dic_all_in.update({'list':list_CAFJourn})
                    dic_all_in.update({'code':'0'})
                    dic_all_in.update({"description":"委託成功"})
            elif xml_list.split('&')[0] in ["url=applyNoticeSignU20","applyNoticeSignU20"]:#期貨契約簽署
                recv_data = dgw_main.bobo_main_socket(list_of_post_,'309')
                dic_recv = dgw_main.tran_future_309(recv_data)#從中菲回來的電文處理204後,轉成dict(N次)
                dic_all_in.update({'statusCode':dgw_main.key_exist_in_object('statusCode',dic_recv)})
                dic_all_in.update({'code':'0'})
            elif xml_list.split('&')[0] in ["url=queryTradeClass2","queryTradeClass2"]:#下單 商品列表
                contract_data_type = '1'
                if dgw_main.key_exist_in_object('type',dic_xml_head_dict) == 'O':
                    contract_data_type = '2'

                list_all_future_contract_data = dgw_main.get_all_future_contract_data('TIMEX',contract_data_type,get_ini_list('TradeID'),get_ini_list('ClassID'),get_ini_list('StkID'))
                dic_all_in.update({'list':list_all_future_contract_data})
                dic_all_in.update({'code':'0'})
                dic_all_in.update({"description":"委託成功"})
            elif xml_list.split('&')[0] in ["url=logout","logout"]:#logout
                try:
                    sqlcmd = "delete from public.tb_gateway_session_info where sid = '"+sid+"'"
                    ApexDB_cursor_.execute(sqlcmd)
                    #del request.session['lucky']#session idno logout
                    #del request.session['LoginResp']#session idno logout
                    dic_all_in.update({'code':'0'})
                    dic_all_in.update({"description":"已登出"})
                except:
                    dic_all_in.update({'code':'9000'})
                    dic_all_in.update({'description':'尚未登入'})
            elif xml_list.split('&')[0] in ["mfcISAPICommand=GetTradeopenclose","GetTradeopenclose"]:#交易時間
                datestr = str(int(str(datetime.datetime.now())[0:4]) - 1911) + "/" + str(datetime.datetime.now())[5:7] + "/" + str(datetime.datetime.now())[8:10]
                timestr = str(datetime.datetime.now())[11:19]
                #證券交易時間
                sqlcmd = "select * from dfh.tb_trade_time"
                ApexDB_cursor_.execute(sqlcmd)
                trade_time_results = ApexDB_cursor_.fetchall()
                #期貨交易時間
                p = HttpResponse("<TARoot>\
<TASystem client='210.202.1.1' inte='2.1.2.1' module='TASBSComMgmt' oper='10' page='xml' server='ap-test.dcn.com.tw' />\
<TAUser addr='210.202.1.1' brdt='50/01/01' cert='-----2--' comp='9999' cona='寶碩' cosy='9999' curl='-------------------------------' emcu='187635' idno='' lang='0' mode='2' name='台中商銀' pkic='-------0' pref='0' rela='---------------------987654--10' sett='' sign='----3---' />\
<TAStatus action='' code='0' count='4' date='" + datestr + "' time='" + timestr + "' />\
<SECTime open='" + trade_time_results[0][1][:2] + ":" + trade_time_results[0][1][2:] + ":00' close='" + trade_time_results[0][2][:2] + ":" + trade_time_results[0][2][2:] + ":00'/>\
<ODDTime open='" + trade_time_results[0][3][:2] + ":" + trade_time_results[0][3][2:] + ":00' close='" + trade_time_results[0][4][:2] + ":" + trade_time_results[0][4][2:] + ":00'/>\
<FIXTime open='" + trade_time_results[0][5][:2] + ":" + trade_time_results[0][5][2:] + ":00' close='" + trade_time_results[0][6][:2] + ":" + trade_time_results[0][6][2:] + ":00'/>\
<EMGTime open='" + trade_time_results[0][10][:2] + ":" + trade_time_results[0][10][2:] + ":00' close='" + trade_time_results[0][11][:2] + ":" + trade_time_results[0][11][2:] + ":00'/>\
<HKTime open='" + trade_time_results[0][10][:2] + ":" + trade_time_results[0][10][2:] + ":00' close='" + trade_time_results[0][11][:2] + ":" + trade_time_results[0][11][2:] + ":00'/>\
<FUTTimes tacontainer='3'>\
<FUTTime  contract = 'TXO' mark = 'D' open='09:50:30' close='16:50:30'/>\
<FUTTime  contract = 'TXF' mark = 'D' open='09:50:30' close='16:50:30'/>\
<FUTTime  contract = 'MXF' mark = 'N' open='13:50:00' close='20:00:00'/>\
</FUTTimes >\
<TAFinish />\
</TARoot>",content_type="text/xml; charset=" + xml_encode_charset)
            else:
                if request.method == 'GET':
                    write_log_txt('====GET1====')
                    #proxy = {'HTTPS': '117.85.105.170:808'}
                    r = requests.get(list_of_post_, cookies=cookies, headers=header_dic)#proxies=proxy
                elif request.method == 'POST':
                    write_log_txt('====POST1====')
                    result = ""
                    post_dic = {}
                    for item in str(request.body.decode('big5')).split('&'):
                        if item.split('=')[0] == 'tasignature':
                            remake_str = item.split('=')[1].replace('\r\n',chr(0x0d)+chr(0x0a))
                        elif item.split('=')[0] == 'tasignfield':
                            remake_str = item.split('=')[1]
                        else:
                            remake_str = item.split('=')[1]
                        result=result+"&"+item.split('=')[0]+"="+remake_str
                    result.replace('&','',1)
                    if result.find("&tasignature") > 0:#20170809 log不要寫一堆驗簽亂碼
                        write_log_txt(result[:result.find("&tasignature")])
                    r = requests.post(og_str, headers=header_dic, data=result, cookies=cookies)
                else:
                    write_log_txt('====no hide plz===='+xml_list.split('&')[0])
                    r = requests.get(og_str,cookies=cookies)
                write_dazu_response_log_txt(r.content.decode('cp950'),dazu_response_log_path+xml_list.split('&')[0].split('?')[1]+"_"+str(datetime.datetime.now())[0:10].replace('-','')+"_"+str(datetime.datetime.now())[11:23].replace(':','').replace('.','')+".xml")
                p = HttpResponse(str(r.content.decode('cp950',errors='ignore')).replace("Big5", "utf-8").encode('utf8'),content_type="text/xml; charset="+xml_encode_charset)
                return p
        except:
            write_log_txt('redirect_dgw=' + str(sys.exc_info()))
            p = HttpResponse("<TARoot><ERROR>" + str(sys.exc_info()).replace("<","").replace("(","").replace(">","").replace(")","") + "</ERROR></TARoot>",content_type="text/xml; charset=" + xml_encode_charset)
            return p
        ApexDB_cursor_.close()
    #20170217
    else:
        dic_all_in.update({'code':'-1000'})
        dic_all_in.update({'description':'您無該帳號權限'})
        """
        datestr = str(int(str(datetime.datetime.now())[0:4]) - 1911) + "/" + str(datetime.datetime.now())[5:7] + "/" + str(datetime.datetime.now())[8:10]
        timestr = str(datetime.datetime.now())[11:19]
        #20170223 登入其他時間資訊
        return HttpResponse("<TARoot>\
                            <TASystem module='TANCCCalMgmt' page='xml' inte='14.15.1.1' oper='10' server='ap-test.dcn.com.tw' client='210.202.1.1'/>\
                            <TAUser idno='A100030009' name='寶碩' pkic='0' cert='-----2--' sign='----3---' lang='0' pref='0' comp='0' cosy='646' cona='總公司' mode='0' emno='30009' sales='' clerk='30009' dept='' addr='192.168.50.4'></TAUser>\
                            <TAStatus code='0' count='1' date='" + datestr + "' time='" + timestr + "'/>\
                            <NCCCALND perm='---mawrb' mark='TAIEX' mkna='台灣集中市集' coun='TW' cuna='台灣' date='" + datestr + "' nextdate='" + datestr + "' comp='0' cosy='646' cona='總公司' stts='32767'/>\
                            <TAFinish/></TARoot>",content_type="text/xml; charset=" + xml_encode_charset)
    """
    return response_mode_switch(request,dic_all_in,response_mode)

#region view common fuction
def write_log_txt(object):
    f = open(logpath + logtxt_filename,"a")

    f.write("\n[" + str(datetime.datetime.now()) + "]" + str(object))
    f.close()

# 取出 ini 中的設定
def get_ini_str(section, key):
    config_ = configparser.ConfigParser()
    #config_.read('DataImport.ini')
    config_.read(logpath + "dcn_dgw.ini")
    return config_.get(section, key)

# 取出 ini 中的設定
def get_ini_list(section):
    config_ = configparser.ConfigParser()
    config_.read(logpath + "dcn_dgw.ini")
    return config_.items(section)

# 建一個 order server DB_cursor_
def build_order_server_DB_cursor_():
    #建立order_server_DB_cursor_
    DB_IP_ = get_ini_str("DBconfig", "DB_IP_")
    DB_Port_ = get_ini_str("DBconfig", "DB_Port_")
    DB_DB_ = get_ini_str("DBconfig", "DB_DB_")
    DB_User_ = get_ini_str("DBconfig", "DB_Name_")
    DB_Pwd_ = get_ini_str("DBconfig", "DB_Pwd_")

    order_server_DB_str_ = "host=" + DB_IP_ + " port=" + DB_Port_ + " user=" + DB_User_ + " dbname=" + DB_DB_ + " password=" + DB_Pwd_
    
    try:
        DB_conn_ = psycopg2.connect(order_server_DB_str_)
    except:
        write_log_txt("==== build_order_server_DB_cursor_ ERROR ====" + str(sys.exc_info()))
        sys.exit(0)    
    
    DB_conn_.autocommit = True
    DB_conn_.set_client_encoding('UTF8')
    order_server_DB_cursor_ = DB_conn_.cursor()
    return order_server_DB_cursor_

#建立ApexDB_cursor_
def build_ApexDB_cursor_():
    ApexDB_IP_ = get_ini_str("Apex", "DB_IP_")
    ApexDB_Port_ = get_ini_str("Apex", "DB_Port_")
    ApexDB_DB_ = get_ini_str("Apex", "DB_DB_")
    ApexDB_User_ = get_ini_str("Apex", "DB_Name_")
    ApexDB_Pwd_ = get_ini_str("Apex", "DB_Pwd_")

    ApexDB_str_ = "host=" + ApexDB_IP_ + " port=" + ApexDB_Port_ + " user=" + ApexDB_User_ + " dbname=" + ApexDB_DB_ + " password=" + ApexDB_Pwd_
    
    try:
        ApexDB_conn_ = psycopg2.connect(ApexDB_str_)
    except:
        write_log_txt("==== build_ApexDB_cursor_ ERROR ====" + str(sys.exc_info()))
        sys.exit(0)    
    
    ApexDB_conn_.autocommit = True
    ApexDB_conn_.set_client_encoding('UTF8')
    ApexDB_cursor_ = ApexDB_conn_.cursor()
    return ApexDB_cursor_

def build_xml_head(list_of_post):
    result_dict = {}
    item_list = list_of_post.split('&')
    for item in item_list:
        if item.split('=')[0] == 'tasignature':
            result_dict.update({'tasignature':item.replace('tasignature=','').strip()})
        elif len(item.split('=')) == 2:
            result_dict.update({item.split('=')[0]:item.split('=')[1]})
        elif len(item.split('=')) == 1:
            result_dict.update({item.split('=')[0]:item.split('=')[0]})
        else:
            result_dict.update({item.split('=')[0]:''})
    return result_dict
# post方法內隱藏的參數轉成get型式url
def post_to_url(list_of_post_):
    result = ""
    for item in list_of_post_.split('&'):
        if item.split('=')[0] == 'tasignature':
            remake_str = item.replace('tasignature=','').strip()
            result = result + "&" + item.split('=')[0] + "=" + remake_str
        else:
            if len(item.split('=')) == 2:
                remake_str = parse.quote(item.split('=')[1],encoding='cp950')
                result = result + "&" + item.split('=')[0] + "=" + remake_str
            elif len(item.split('=')) == 1:
                result = result + item.split('=')[0]
    if result.find('&') == 0:
        result = result.replace('&','',1)#重組一下做成URL的樣子
    return result
#Session Object權限控管
def Session_search(sid_,sett_,ApexDB_cursor_):
    try:
        sqlcmd = "SELECT scontent,expire_time from public.tb_gateway_session_info where sid = '"+sid_+"'"
        ApexDB_cursor_.execute(sqlcmd)
        s_obj = ApexDB_cursor_.fetchall()[0][0]

        #write_log_txt('====Session_search done==== sid=' + sid_)
        #write_log_txt("s_obj=")
        #write_log_txt("s_obj="+s_obj)
        stock_account_list = s_obj['list_GetMarkPass']['stock_account_list']
        futures_account_list = s_obj['list_GetMarkPass']['futures_account_list']

        for item in stock_account_list:
            if str(item['sett']).strip() == str(sett_).strip().rjust(7,'0'):
                return True
        for item in futures_account_list:
            if str(item['sett']).strip() == str(sett_).strip().rjust(7,'0'):
                return True
    except:
        write_log_txt('====Session_search error==== sid=' + sid_+", sett="+sett_)
        pass
    if Test_Server_view_mode:
        return True#59 測試機 不鎖權限
    return False
# proxy每日初始狀態
def proxy_server_start_active(request):
    global UK_temp
    global UK_temp_time
    today = str(datetime.datetime.now())[0:10].replace('-','')
    UK_temp = dgw_main.get_UK_future(get_ini_str("Future", "ip"), get_ini_str("Future", "UserID"), get_ini_str("Future", "UserPsw")).UK
    UK_temp_time = str(datetime.datetime.now())
    
    ApexDB_cursor_ = build_ApexDB_cursor_()
    order_server_DB_cursor_ = build_order_server_DB_cursor_()
    #ptype = 10 是local端測試時暫時改的
    check_sqlstr = "select tvalue from public.tb_trade_parameter where ptype = '08'"
    order_server_DB_cursor_.execute(check_sqlstr)
    check_result = order_server_DB_cursor_.fetchall()
    write_log_txt(str(check_result[0][0]) + "==== proxy_server_Daily_Clean_start_active ====" + str(today))
    try:
        #清盤標記必須小於今天
        if str(check_result[0][0]) < str(today):
            sqlstr = "insert into dfhf.tb_future_pxbs_history(tdate,extm,dnflag,bhno,future_account,comm,symb,bs,lino,kind\
,orsh,duov,nesh,orpr,orpt,ortr,orcn,orse,prodtype,cdi,rowdata) \
select tdate, extm, dnflag, bhno, future_account, comm, symb, bs, lino, kind\
, orsh, duov, nesh, orpr, orpt, ortr, orcn, orse, prodtype, cdi, rowdata from dfhf.tb_future_pxbs where tdate !='" + today + "';\
insert into dfhf.tb_future_pxmh_history (tdate, extm, dnflag, future_account, comm, symb, bs, lino, lots, pric, orse, prodtype, rowdata) \
select tdate, extm, dnflag, future_account, comm, symb, bs, lino, lots, pric, orse, prodtype, rowdata from dfhf.tb_future_pxmh where tdate !='" + today + "';\
insert into dfhf.tb_future_detail_history(tdate,extm,dnflag,future_account,comm,symb,bs,lino,lots,pric,orse,prodtype,cdi)\
select tdate,extm,dnflag,future_account,comm,symb,bs,lino,lots,pric,orse,prodtype,cdi from dfhf.tb_future_detail where tdate !='" + today + "';\
delete from dfhf.tb_future_detail where tdate !='" + today + "';\
delete from dfhf.tb_future_pxbs where tdate !='" + today + "';\
delete from dfhf.tb_future_pxmh where tdate !='" + today + "';"
            ApexDB_cursor_.execute(sqlstr)
            update_sqlstr = "update public.tb_trade_parameter set tvalue = '" + today + "', cuser = '" + str(datetime.datetime.now())[11:19] + "', last_update = now() at time zone 'CCT' where ptype = '08'"
            order_server_DB_cursor_.execute(update_sqlstr)
            write_log_txt("==== proxy_server_Daily_Clean complete ====")
    except:
        write_log_txt("==== proxy_server_Daily_Clean error ====" + str(sys.exc_info()))
    #20170405 要加入一個清空的步驟
    ApexDB_cursor_.close()
    order_server_DB_cursor_.close()
    p = HttpResponse("<TARoot><server_init>\
                    <UK>" + UK_temp + "</UK>\
                    <Daily_Clean_value>" + str(check_result[0][0]) + "</Daily_Clean_value>\
                    <today>" + today + "</today>\
                    </server_init></TARoot>",content_type="text/xml; charset=" + xml_encode_charset)
    return p
# proxy暫存&狀態監控
def proxy_server_status(request):
    global UK_temp
    global UK_temp_time
    #20170405 會再新增客戶資料暫存
    p = HttpResponse("<TARoot><server_temp>\
                    <UK>" + UK_temp + "</UK>\
                    <UK_temp_time>" + UK_temp_time + "</UK_temp_time>\
                    </server_temp></TARoot>",content_type="text/xml; charset=" + xml_encode_charset)
    return p

def default(request):
    #不要覆蓋
    return HttpResponse("<TARoot><default>預設回應</default><default2>有時候會放些測試資料</default2></TARoot>",content_type="text/xml; charset=" + xml_encode_charset)
#endregion view common fuction
#region ==== 使用範例 ====
#login 000 登入
#http://203.69.48.29/redirect_dgw/BAServlet?https://192.168.200.85:8080/dachang/BAServlet?&url=login&TAAccountMode=1&comp=6460&idno=A123456789&sett=&pass=12345678&tapage=xml
#000 登入 錯誤 <TAStatus code="0000004" count="0" description="查無帳務資料"/>
#http://203.69.48.29/redirect_dgw/BAServlet?https://192.168.200.85:8080/dachang/BAServlet?&url=login&TAAccountMode=1&comp=6460&idno=A123477789&pass=12345678&tapage=xml
#登出
#http://203.69.48.29/redirect_dgw/BAServlet?http://192.168.200.85:8080/dachang/BAServlet?&url=CheckSession

#GetLoginResp 001 查詢客戶資料 page load check
#http://203.69.48.29/redirect_dgw/BAServlet?https://192.168.200.85:8080/dachang/BAServlet?&url=GetLoginResp&idno=A123456789
#001 查詢客戶資料 錯誤
#http://203.69.48.29/redirect_dgw/BAServlet?https://192.168.200.85:8080/dachang/BAServlet?&url=GetLoginResp2&idno=A123499999

#changeUserPassword 002 變更密碼 變更出金密碼
#變更密碼 
#http://203.69.48.29/redirect_dgw/BAServlet?https://192.168.200.85:8080/dachang/BAServlet?&url=changeUserPassword&oldpass=1234567&pass=88888888&cate=0&idno=A123456789
#變更出金密碼
#http://203.69.48.29/redirect_dgw/BAServlet?https://192.168.200.85:8080/dachang/BAServlet?&url=changeUserPassword&oldpass=1234567&pass=99999999&cate=8&idno=A123456789

#reportDataT20 100 期貨下單
#http://203.69.48.29/redirect_dgw/BAServlet?https://192.168.200.85:8080/dachang/BAServlet?&url=reportDataT20&execType=0&cosy=F039000&type=0&lino=1&date=106/12/14&comp=F039000&sett=6666666&mark=TAIMEX&symb=FITX&exdt=201801&stpr=undefined&capu=0&losh=1&seed=undefined&sesp=undefined&secp=0&sels=0&orsh=2&orpr=9523&orpt=0&ortr=%20&orcn=0&stockid=TXFA8&orderqty=2&tasignfield=type,lino,date,comp,sett,mark,symb,exdt,stpr,capu,losh,seed,sesp,secp,sels,orsh,orpr,orpt,ortr,orcn&tasignature=

#reportDataT20 101 期貨改單
#http://203.69.48.29/redirect_dgw/BAServlet?
#改量
#https://192.168.200.85:8080/dachang/BAServlet?&url=reportDataT20&execType=5&cosy=F039000&type=20&lino=1&date=1061122&comp=undefined&sett=6666666&mark=undefined&symb=MXFI8&exdt=undefined&stpr=undefined&capu=undefined&losh=B&seed=undefined&sesp=undefined&secp=undefined&sels=undefined&orsh=1&orpr=9270.0000&orpt=L&ortr=0&orcn=R&comm=PP727&orse=0iW208Fv&InputSource2=DS1&orst=1&orderqty=1&tasignfield=type,lino,date,comp,sett,mark,symb,exdt,stpr,capu,losh,seed,sesp,secp,sels,orsh,orpr,orpt,ortr,orcn&tasignature=
#改價
#https://192.168.200.85:8080/dachang/BAServlet?&url=reportDataT20&execType=M&cosy=F039000&type=15&lino=1&date=1061122&comp=undefined&sett=6666666&mark=undefined&symb=MXFI8&exdt=undefined&stpr=undefined&capu=undefined&losh=B&seed=undefined&sesp=undefined&secp=undefined&sels=undefined&orsh=1&orpr=9271&orpt=0&ortr=0&orcn=0&comm=PJ886&orse=0iW206IP&InputSource2=DS1&orst=1&orderqty=1&tasignfield=type,lino,date,comp,sett,mark,symb,exdt,stpr,capu,losh,seed,sesp,secp,sels,orsh,orpr,orpt,ortr,orcn&tasignature=
#刪單
#https://192.168.200.85:8080/dachang/BAServlet?&url=reportDataT20&execType=4&cosy=F039000&type=30&lino=1&date=1061122&comp=undefined&sett=6666666&mark=undefined&symb=MXFI8&exdt=undefined&stpr=undefined&capu=undefined&losh=B&seed=undefined&sesp=undefined&secp=undefined&sels=undefined&orsh=1&orpr=9271.0000&orpt=L&ortr=0&orcn=R&comm=PK081&orse=0iW206IP&InputSource2=DS1&orst=1&orderqty=1&tasignfield=type,lino,date,comp,sett,mark,symb,exdt,stpr,capu,losh,seed,sesp,secp,sels,orsh,orpr,orpt,ortr,orcn&tasignature=

#reportDataB20 201 期貨庫存
#http://203.69.48.29/redirect_dgw/BAServlet?https://192.168.200.85:8080/dachang/
#BAServlet?&url=reportDataB20&cosy=F039000&sett=9802469

#204 期貨庫存
#http://203.69.48.29/redirect_dgw/BAServlet?
#BAServlet?&url=reportDataB22&cosy=F039000&sett=9802469&date=1060920&date1=1060925

#reportDataB21 207 權益數
#http://203.69.48.29/redirect_dgw/BAServlet?https://192.168.200.85:8080/dachang/BAServlet?&url=reportDataB21&cosy=F039000&sett=6666666

#reportDataT21 208+211 期貨委託回補
#http://203.69.48.29/redirect_dgw/BAServlet?&url=reportDataT21&cosy=F039000&sett=6666666&page=500&date=107/02/27&date1=107/03/08&_=1510917300911

#reportDataT22 209+212 期貨成交回補
#http://203.69.48.29/redirect_dgw/BAServlet?https://192.168.200.85:8080/dachang/BAServlet?&url=reportDataT22&cosy=F039000&sett=6666666&date=null1117&date1=null1117&_=1510917300426

#出金密碼檢核
#http://192.168.200.85:8080/dachang/BAServlet?&url=checkUserPassword&pwd=12345678&_=1514963453594&sett =6666666

#reportDataB50 出金申請
#http://203.69.48.29/redirect_dgw/BAServlet?
#http://192.168.200.85:8080/dachang/BAServlet?&url=reportDataB50&cosy=F039000&sett=6666666&TranType=W&Currency=TWD&Amount=20&ExecType=1&BankID=8220174&BankAccoount=123456789&TradeDate=106/11/21&tasignfield=F039000,6666666,20,8220174,123456789,106/11/21,1,Y&TASIGNATURE=
#取消出金
#http://192.168.200.85:8080/dachang/BAServlet?&url=reportDataB50&cosy=F039000&sett=6666666&TranType=W&Currency=TWD&Amount=20.00&ExecType=2
#&BankID=8220174&BankAccoount=20680100083899&TradeDate=1061121&ApplySource=DS2&ApplyNo=100001&tasignfield=F039000,6666666,20.00,8220174,20680100083899,1061121,2,Y&TASIGNATURE=

#reportDataB51
#http://203.69.48.29/redirect_dgw/BAServlet?
#http://192.168.200.85:8080/dachang/BAServlet?&url=reportDataB51&cosy=F039000&sett=6666666&date=1061201&date1=1061220

#applyNoticeSignU20 期貨契約簽署
#http://203.69.48.29/redirect_dgw/BAServlet?https://192.168.200.85:8080/dachang/BAServlet?&url=applyNoticeSignU20&execType=06&cosy=F039000&sett=6666666&date=106/12/07&idno=A123456789&tasignfield=type,comp,sett&TASIGNATURE=
#endregion ==== 使用範例 ====
#更新紀錄 20180316 16:05