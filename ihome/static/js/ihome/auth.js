function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}


$(document).ready(function () {
    // alert("hello")
    // 查询用户的实名认证信息
    $.get("/api/v1.0/users/auth", function (resp) {
        // 用户未登录
        // alert("Hello")
        if (resp.errno == "4101") {
            location.href = "/login.html";
        }
        else if (resp.errno == "0") {
            // 如果返回的数据中real_name & id_card 不未null，表示用户有填写实名信息
            if (resp.data.real_name && resp.data.id_card) {
                $("#real-name").val(resp.data.real_name);
                $("#id-card").val(resp.data.id_card);
                // 给input添加disabled 属性，禁止用户修改
                $("#real-name").prop("disabled", true);
                $("#id-card").prop("disabled", true);
                // 隐藏提交保存按钮
                $("#form-auth>input[type=submit]").hide();
            }
        }
        else {
            alert(resp.errmsg)
        }
    }, "json");

    // 管理实名信息表单的提交行为
    $("#form-auth").submit(function (e) {
        e.preventDefault();
        // 如果用户没有填写完整，展示错误信息
        var realName = $("#real-name").val();
        var idCard = $("#id-card").val();
        if (realName == "" || idCard == "") {
            $(".error-msg").show();
        }

        // 将表单数据转换为json数据
        var data = {
            real_name: realName,
            id_card: idCard
        };
        var jsonData = JSON.stringify(data);

        // 向后端发送请求
        $.ajax({
            url: "/api/v1.0/users/auth",
            type: "post",
            data: jsonData,
            contentType: "application/json",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    $(".error-msg").hide();
                    // 显示成功的提示信息
                    showSuccessMsg();
                    $("#real-name").prop("disabled", true);
                    $("#id-card").prop("disabled", true);
                    $("#form-auth>input[type=submit]").hide();
                }
            }
        })
    })
});