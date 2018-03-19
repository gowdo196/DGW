/*=============================================================================
Project	: [DCN GateWay] Project.
Date 	: 2018.01.25
Author 	: al0926783757@mail.apex.com.tw
Desc 	: DCN GateWay session control table
=============================================================================*/
drop table if exists public.tb_gateway_session_info cascade;

create table public.tb_gateway_session_info
(
"idno" varchar(10),
"sid" varchar(64) not null,
"scontent" json,
"expire_time" varchar(26),
"log_time" timestamp(6) DEFAULT timezone('CCT'::text, now()) NOT NULL,
CONSTRAINT "pk_tb_gateway_session_info" PRIMARY KEY ("sid")
);

COMMENT ON TABLE  public.tb_gateway_session_info          IS 'DCN GateWay session control table';

COMMENT ON COLUMN public.tb_gateway_session_info."idno"		            IS '身分證統一編號';
COMMENT ON COLUMN public.tb_gateway_session_info."sid"	                IS 'apex_session_id';
COMMENT ON COLUMN public.tb_gateway_session_info."scontent"            IS 'session value';
COMMENT ON COLUMN public.tb_gateway_session_info."expire_time"	                IS '過期時間';
COMMENT ON COLUMN public.tb_gateway_session_info.log_time                      IS 'LOG時間';

CREATE INDEX "tb_gateway_session_info_orse_idx" ON "public"."tb_gateway_session_info" USING btree ("idno");
CREATE INDEX "tb_gateway_session_info_log_time_idx" ON "public"."tb_gateway_session_info" USING btree ("log_time");


--insert 
insert into public.tb_gateway_session_info ("idno","sid","scontent","expire_time")
VALUES ('A123456789','fca819a8f7a89b1021a3047c0f03c7b9379ba366c0d6ade8ef4b2d81084772dd','{ "customer": "John Doe", "items": {"product": "Beer","qty": 6}}','2018-01-29 19:29:47.493900');
insert into public.tb_gateway_session_info ("idno","sid","scontent","expire_time")
VALUES ('A123456789','fca819a8f7a89b1021a3047c0f03c7b9379ba366c0d6ade8ef4b2d81084772dd','{ "customer": "John Doe", "items": {"product": "Beer","qty": 6}}','2018-02-09 19:29:47.493900');

insert into public.tb_gateway_session_info ("idno","sid","scontent","expire_time")
VALUES ('A123456789','6cdd43d3c124bd3440031813e12b0ab41cf18494ba841b92fe906ae8e792f0ce','WTF','');

--DELETE
delete from public.tb_gateway_session_info where sid = 'fca819a8f7a89b1021a3047c0f03c7b9379ba366c0d6ade8ef4b2d81084772dd'

--SELECT
SELECT scontent from public.tb_gateway_session_info where sid = 'fca819a8f7a89b1021a3047c0f03c7b9379ba366c0d6ade8ef4b2d81084772dd'