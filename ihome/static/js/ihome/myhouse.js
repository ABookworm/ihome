$(document).ready(function(){
    // $(".auth-warn").show();
    $.get("/api/v1.0/users/auth", function (resp) {
        if (resp.errno == "4101") {
            // 用户未登录
            location.href == "/logion.html";
        }
        else if (resp.errno = "0") {
            // 未认证的用户，在页面中搜索，“去认证”的按钮
            if (!(resp.data.real_name && resp.data.id_card)) {
                $(".auth-warn").show();
                return;
            }
            // 已认证的用户，请求其之前发布的房源信息
            $.get("/api/v1.0/user/houses", function (resp) {
                if (resp.errno == "0") {
                    $("#houses-list").html(template("houses-list-tmpl", {houses: resp.data.houses}))
                }
                else {
                    $("#houses-list").html(template("houses-list-tmpl", {houses: resp.data.houses}))

                }
            })
        }

    })
})