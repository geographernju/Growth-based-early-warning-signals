library(treenetproc)
library(dplyr)
infile<-"D:/data/Dendrometer.csv"
outdir<-"D:/data/Processed data/TWD"
dir.create(outdir,recursive=TRUE,showWarnings=FALSE)
df<-read.csv(infile,check.names=FALSE,stringsAsFactors=FALSE)
df$Date<-trimws(gsub("\\s+"," ",df$Date))
df$Date<-as.POSIXct(df$Date,format="%Y/%m/%d %H:%M:%S",tz="Etc/GMT-8")
if(all(is.na(df$Date)))stop("Unrecognized time format in the Date column; expected a format such as 2016/5/15 17:00:00")
date_ranges<-data.frame(start=as.Date(c("2019-06-14","2020-04-16","2021-04-01","2022-04-13","2023-04-06")),end=as.Date(c("2019-09-13","2020-09-01","2021-09-20","2022-08-29","2023-09-10")),stringsAsFactors=FALSE)
tree_cols<-setdiff(names(df),"Date")
daily_twd_list<-list()
log_list<-list()
for(tree in tree_cols){
  tree_dat<-df[,c("Date",tree)]
  names(tree_dat)<-c("Date","value")
  tree_dat$value<-as.numeric(tree_dat$value)
  tree_dat<-tree_dat[!is.na(tree_dat$Date),]
  tree_dat<-tree_dat[order(tree_dat$Date),]
  tree_out_list<-list()
  for(i in seq_len(nrow(date_ranges))){
    st<-date_ranges$start[i]
    ed<-date_ranges$end[i]
    sub<-tree_dat[as.Date(tree_dat$Date)>=st & as.Date(tree_dat$Date)<=ed,]
    sub<-sub[!is.na(sub$value),]
    if(nrow(sub)<20){
      log_list[[length(log_list)+1]]<-data.frame(tree=tree,start=as.character(st),end=as.character(ed),status="skip",message="Too few valid records",stringsAsFactors=FALSE)
      next
    }
    input_l0<-data.frame(ts=format(sub$Date,"%Y-%m-%d %H:%M:%S"),value=sub$value,check.names=FALSE,stringsAsFactors=FALSE)
    l1<-tryCatch(proc_L1(data_L0=input_l0,reso=30,input="wide",date_format="%Y-%m-%d %H:%M:%S",tz="Etc/GMT-8"),error=function(e)e)
    if(inherits(l1,"error")){
      log_list[[length(log_list)+1]]<-data.frame(tree=tree,start=as.character(st),end=as.character(ed),status="L1_failed",message=conditionMessage(l1),stringsAsFactors=FALSE)
      next
    }
    l2<-tryCatch(suppressMessages(suppressWarnings(proc_dendro_L2(dendro_L1=l1,plot=FALSE,plot_export=FALSE,tz="Etc/GMT-8"))),error=function(e)e)
    if(inherits(l2,"error")){
      log_list[[length(log_list)+1]]<-data.frame(tree=tree,start=as.character(st),end=as.character(ed),status="L2_failed",message=conditionMessage(l2),stringsAsFactors=FALSE)
      next
    }
    res<-as.data.frame(l2)
    if(!all(c("ts","twd")%in%names(res))){
      log_list[[length(log_list)+1]]<-data.frame(tree=tree,start=as.character(st),end=as.character(ed),status="missing_columns",message="L2 results are missing the ts or twd column",stringsAsFactors=FALSE)
      next
    }
    res$ts<-as.POSIXct(res$ts,format="%Y-%m-%d %H:%M:%S",tz="Etc/GMT-8")
    res<-res[!is.na(res$ts),]
    res<-res[order(res$ts),]
    res$Date<-as.Date(res$ts,tz="Etc/GMT-8")
    res<-res[res$Date>=st & res$Date<=ed,]
    if(nrow(res)==0){
      log_list[[length(log_list)+1]]<-data.frame(tree=tree,start=as.character(st),end=as.character(ed),status="empty_after_L2",message="No valid results after L2 processing",stringsAsFactors=FALSE)
      next
    }
    daily_twd<-res%>%group_by(Date)%>%summarise(value=max(twd,na.rm=TRUE),.groups="drop")
    daily_twd$value[is.infinite(daily_twd$value)]<-NA
    daily_twd<-data.frame(Date=format(daily_twd$Date,"%Y/%m/%d"),x=daily_twd$value,check.names=FALSE,stringsAsFactors=FALSE)
    names(daily_twd)[2]<-tree
    tree_out_list[[length(tree_out_list)+1]]<-daily_twd
    log_list[[length(log_list)+1]]<-data.frame(tree=tree,start=as.character(st),end=as.character(ed),status="ok",message=paste0("Daily record count=",nrow(daily_twd)),stringsAsFactors=FALSE)
  }
  if(length(tree_out_list)>0){
    tree_all<-bind_rows(tree_out_list)
    tree_all<-tree_all[!duplicated(tree_all$Date),]
    tree_all<-tree_all[order(as.Date(tree_all$Date,format="%Y/%m/%d")),]
    daily_twd_list[[tree]]<-tree_all
  }
}
if(length(daily_twd_list)==0)stop("Failed to extract daily tree water deficit; check the raw data, time format, or treenetproc version")
daily_twd_all<-Reduce(function(x,y)full_join(x,y,by="Date"),daily_twd_list)
daily_twd_all<-daily_twd_all[order(as.Date(daily_twd_all$Date,format="%Y/%m/%d")),]
sph_cols<-c("Date",names(daily_twd_all)[grepl("SPH",names(daily_twd_all),ignore.case=FALSE)])
spl_cols<-c("Date",names(daily_twd_all)[grepl("SPL",names(daily_twd_all),ignore.case=FALSE)])
ssl_cols<-c("Date",names(daily_twd_all)[grepl("SSL",names(daily_twd_all),ignore.case=FALSE)])
sph_cols<-unique(sph_cols[sph_cols%in%names(daily_twd_all)])
spl_cols<-unique(spl_cols[spl_cols%in%names(daily_twd_all)])
ssl_cols<-unique(ssl_cols[ssl_cols%in%names(daily_twd_all)])
daily_twd_sph<-daily_twd_all[,sph_cols,drop=FALSE]
daily_twd_spl<-daily_twd_all[,spl_cols,drop=FALSE]
daily_twd_ssl<-daily_twd_all[,ssl_cols,drop=FALSE]
log_all<-bind_rows(log_list)
write.csv(daily_twd_sph,file.path(outdir,"daily_twd_SPH.csv"),row.names=FALSE,fileEncoding="UTF-8")
write.csv(daily_twd_spl,file.path(outdir,"daily_twd_SPL.csv"),row.names=FALSE,fileEncoding="UTF-8")
write.csv(daily_twd_ssl,file.path(outdir,"daily_twd_SSL.csv"),row.names=FALSE,fileEncoding="UTF-8")
write.csv(log_all,file.path(outdir,"daily_twd_log.csv"),row.names=FALSE,fileEncoding="UTF-8")