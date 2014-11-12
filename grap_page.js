var page = require('webpage').create(),
    system = require('system');

if (system.args.length === 1){
    console.log('Usage: grap_page.js <some URL>');
    phantom.exit();
}

//请求url地址
url = system.args[1];

var winNoticeAll = new Array();
var syncReqAll = new Array();
var syncRx = /sync.*\.htm\?/i;
//获取页面中发送的winnotice请求和sync请求
page.onResourceRequested = function (requestData, networkRequest) {
    if(requestData.url.indexOf("http://wn.pos.baidu.com/adx.php?") > -1){
        var winNotice = new Object();
        var winNoticeReq, winNoticeUrl;
        winNotice.winNoticeReq = requestData.url;
        for(var i=0; i < requestData.headers.length; i++) {
            if(requestData.headers[i].name == "Referer") {
                winNotice.referer = requestData.headers[i].value;
            }
        }
        winNoticeAll.push(winNotice);
    } else if(syncRx.test(requestData.url)) {
        var sync = new Object();
        sync.syncReq = requestData.url;
        for(var i=0; i < requestData.headers.length; i++) {
            if(requestData.headers[i].name == "Referer") {
                sync.referer = requestData.headers[i].value;
            }   
        } 
        syncReqAll.push(sync);    
    }
};


page.open(url, function(status) {
    if (status !== 'success') {
        console.log('Unable to access network');
	    phantom.exit();
    }else {
        var content = new Object();
        var adInfo = []
	    var title = page.evaluate(function() {
            return document.title;
        });

        //获取页面中所有的iframe id以及每个iframe的宽高等信息
        var iframe_info = page.evaluate(function() {
            var iframe_info = new Array();
            var logo_info = new Array();
            var ad_id_list = new Array();
            var floor_length;
            var divs = document.getElementsByTagName('div');
            //get the ad's id list in web page.
            for (var i=0; i<divs.length; i++) {
                if(divs[i].attributes != null && divs[i].attributes["id"] != undefined && divs[i].id.indexOf('BAIDU_DUP_wrapper_') > -1) {
                    ad_id_list.push(divs[i].id);
                }
            }
            for (var i=0; i<ad_id_list.length; i++) {
                id_info = document.getElementById(ad_id_list[i]);
                if (id_info) {
                    var iframe = id_info.firstChild;
                    var iframe_id = iframe.getAttribute('id');
                    var iframe_weight = iframe.getAttribute('width');
                    var iframe_height = iframe.getAttribute('height');
                    var iframe_src = iframe.getAttribute('src');
                }
                if (id_info.nextSibling != null) {
                    var first_link = id_info.nextSibling.getAttribute('src');
                    iframe_info.push({
                        iframe_id: iframe_id,
                        iframe_weight: iframe_weight,
                        iframe_height: iframe_height,
                        iframe_first_link: first_link,
                        iframe_second_link:iframe_src
                    });
                }
            }
            return {
                ad_ids: ad_id_list,
                iframe_information: iframe_info
            };
        });
        
        //提取广告内容信息函数
        function getAdframeInfo() {
            return page.evaluate(function() {
                var logo_info = new Array();
                var search_nodes = new Array();
                //var ad_node = document.getElementById('uptown');
                var iframe_body = document.body;
                var logo_node, floor_node,  ad_node, ad_number = 0;
                
                //get the node of the advertisement from web page.
                for(var i=0; i<iframe_body.childNodes.length; i++) {
                    if (iframe_body.childNodes[i] != null && iframe_body.childNodes[i].innerHTML != null) {
                        if (iframe_body.childNodes[i].tagName.toLowerCase() == 'div') {
                            if (iframe_body.childNodes[i].id == 'container' || iframe_body.childNodes[i].id == 'uptown') {
                                ad_node = iframe_body.childNodes[i];
                                var ad_node_id = ad_node.id;
                            }
                        }
                    }
                }

                //get the node of the logo.
                if (ad_node != null) {
                    for(var i=0; i<ad_node.childNodes.length; i++) {
                        if (ad_node.childNodes[i] != null && ad_node.childNodes[i].innerHTML != null) {
                            if (ad_node.childNodes[i].getAttribute('class').match(/.*logo.*/)) {
                                logo_node = ad_node.childNodes[i];
                            }
                        }
                        if (ad_node.childNodes[i] != null && ad_node.childNodes[i].innerHTML != null) {
                            if (ad_node.childNodes[i].id == 'house') {
                                var house_node = uptown.childNodes[i];
                            }
                        }   
                    }
                }

                //获取logo的相关的信息
                if (logo_node != null) {
                    var logo_style = logo_node.getAttribute('class');
                    var logo_title = logo_node.getAttribute('title');
                    var logo_target = logo_node.getAttribute('target');
                    var logo_href = logo_node.getAttribute('href');
                    logo_info.push({
                        logo_style: logo_style,
                        logo_title: logo_title,
                        logo_target: logo_target,
                        logo_href: logo_href
                    });
                }

                //获取container中广告相关信息
                if (ad_node_id == 'container') {
                    var item_num = 0;
                    var item_nodes = new Array();
                    for (var i=0; i<ad_node.childNodes.length; i++) {
                        if (ad_node.childNodes[i] != null && ad_node.childNodes[i].innerHTML != null) {
                            if (ad_node.childNodes[i].getAttribute('class') == 'item') {
                                item_num += 1;
                                item_nodes.push(ad_node.childNodes[i]);
                            }
                        }
                    }

                    //获取广告每个item相关信息
                    if (item_num > 0) {
                        var items_info = new Array();
                        for (var i=0; i<item_num; i++) {
                            var link_info = new Array();
                            var link_nodes = item_nodes[i].getElementsByTagName('a');
                            for (var j=0; j<link_nodes.length; j++) {
                                if (link_nodes[j] != null && link_nodes[j].innerHTML != null) {
                                    if (link_nodes[j].getAttribute('class')) {
                                        var item_class = link_nodes[j].getAttribute('class')
                                    }
                                    else if (link_nodes[j].parentNode.getAttribute('class')) {
                                        var item_class = link_nodes[j].parentNode.getAttribute('class')
                                    }
                                    if (link_nodes[j].target) {
                                        var item_target = link_nodes[j].target;
                                    }   
                                    if (link_nodes[j].href) {
                                        var item_href = link_nodes[j].href;
                                    }
                                    if (link_nodes[j].title) {
                                        var item_title = link_nodes[j].title;
                                    }   
                                    var item_inner_info = link_nodes[j].innerHTML;
                                }   
                                link_info.push({
                                    item_id: link_nodes[j].id,
                                    item_class: item_class,
                                    item_target: item_target,
                                    item_href: item_href,
                                    item_title: item_title,
                                    item_info: item_inner_info
                                });   
                            }
                            items_info.push({
                                item_node: link_info
                            });  
                        } 
                    }
                }
                
                //获取uptown包含的广告信息
                if (ad_node_id == 'uptown') {
                    var floor_num = 0, floor_nodes = new Array(), room_nodes = new Array();
                    for (var i=0; i<house_node.childNodes.length; i++) {
                        if (house_node.childNodes[i] != null && house_node.childNodes[i].innerHTML != null) {
                            if (house_node.childNodes[i].tagName.toLowerCase() == 'tbody') {
                                var tbody_node = house_node.childNodes[i];
                            }
                        }
                    }

                    //获取tbady中的floor节点
                    for (var i=0; i<tbody_node.childNodes.length; i++) {
                        if (tbody_node.childNodes[i] != null && tbody_node.childNodes[i].innerHTML != null) {
                            if (tbody_node.childNodes[i].tagName.toLowerCase() == 'tr' && tbody_node.childNodes[i].id.indexOf('floor') > -1) {
                                floor_num +=1;
                                floor_nodes.push(tbody_node.childNodes[i]);
                            }          
                        }   
                    }

                    //从floor节点中得到room节点
                    function get_room_nodes(root_node) {
                        var root_child_nodes = root_node.childNodes;
                        var target_node;
                        for(var i=0; i<root_child_nodes.length; i++) {
                            if (root_child_nodes[i] != null && root_child_nodes[i].innerHTML != null) {
                                if (root_child_nodes[i].tagName.toLowerCase() == 'td' && root_child_nodes[i].id.indexOf('room') > -1) {
                                    target_node = root_child_nodes[i];
                                    return target_node;
                                }
                            }
                        }
                    }

                    //得到floor节点中的room节点
                    if (floor_num > 0) {
                        var cur_room_node, room_num=0;
                        var room_nodes = new Array();
                        if (floor_num > 1) {
                            for (var i=0; i<floor_nodes.length; i++) {
                                cur_room_node = get_room_nodes(floor_nodes[i]);
                                room_nodes.push(cur_room_node);
                            }
                        } else {
                            var cur_node_child = floor_nodes[0].childNodes;
                            for (var i=0; i<cur_node_child.length; i++) {
                                if (cur_node_child[i] != null && cur_node_child[i].innerHTML != null) {
                                    if (cur_node_child[i].tagName.toLowerCase() == 'td' && cur_node_child[i].id.indexOf('room') > -1) {
                                        room_nodes.push(cur_node_child[i]);
                                    }
                                }
                            }
                        }
                        room_num = room_nodes.length;
                    }
                    
                    //得到room节点中广告各个item的信息
                    if (room_num > 0) {
                        var items_info = new Array();
                        for (var i=0; i<room_num; i++) {
                            var link_info = new Array();
                            //获得room节点下含有id属性的<a>元素
                            var link_nodes = room_nodes[i].querySelectorAll("a[id]");

                            for (var j=0; j<link_nodes.length; j++) {
                                if (link_nodes[j] != null && link_nodes[j].innerHTML != null) {
                                    if (link_nodes[j].target) {
                                        var item_target = link_nodes[j].target;
                                    }
                                    if (link_nodes[j].getAttribute('class')) {
                                        var item_class = link_nodes[j].getAttribute('class');
                                    }
                                    var item_href = link_nodes[j].href;
                                    var item_inner_info = link_nodes[j].innerHTML;
                                }
                                link_info.push({
                                    item_id: room_nodes[i].id,
                                    item_class: item_class,
                                    item_target: item_target,
                                    item_href: item_href,
                                    item_info: item_inner_info
                                });   
                            }
                            items_info.push({
                                item_node: link_info
                            });
                        }
                    }
                }

                return {
                    logo_information: logo_info,
                    floor_number: floor_num,
                    room_number: room_num,
                    item_num: item_num,
                    items_information: items_info
                }
            });
        }

        //判断页面中是否存在iframe，如果存在则跳转到iframe中去提取广告
        if (iframe_info.ad_ids.length != 0) {
            for (var i=0; i<iframe_info.ad_ids.length; i++) {
                page.switchToFrame(iframe_info.iframe_information[i].iframe_id);
                adframeInfo = getAdframeInfo();
                adInfo.push(adframeInfo);
                page.switchToMainFrame();
            }
        } else {
            adframeInfo = getAdframeInfo();
            adInfo.push(adframeInfo);
        }

        content.title = title;
        content.winnotice = winNoticeAll;
        content.sync = syncReqAll;
        content.adframe_info = adInfo;
        content.iframe_info = iframe_info;
        //输出页面中所有的信息
        console.log(JSON.stringify(content, undefined, 4));
    }
    phantom.exit();
});

