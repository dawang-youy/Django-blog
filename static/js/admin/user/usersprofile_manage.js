$(function () {
  let $e = window.wangEditor;
  window.editor = new $e('#usersprofile-motto');
  window.editor.create();
  window.editor.txt.html($('#usersprofile-motto').data('con'));
  let $bornTime = $("input[name=born_time]");
  const config = {
    // 自动关闭
    autoclose: true,
    // 日期格式
    format: 'yyyy/mm/dd',
    // 选择语言为中文
    language: 'zh-CN',
    // 优化样式
    showButtonPanel: true,
    // 高亮今天
    todayHighlight: true,
    // 是否在周行的左侧显示周数
    calendarWeeks: true,
    // 清除
    clearBtn: true,
    // 0 ~11  网站上线的时候
    startDate: new Date(2018, 10, 1),
    // 今天
    endDate: new Date(),
  };
  $bornTime.datepicker(config);
  // 获取修改之前的值
  let noUsersProfileNickname = $("input[name='nickname']").val();
  let noUsersProfileBorndate = $("input[name='born_time']").val();
  let noUsersProfileGender = $("#gender").val();
  let noUsersProfileMotto = window.editor.txt.html();

  // ================== 删除用户信息 ================
  let $userDel = $(".btn-del");  // 1. 获取删除按钮
  $userDel.click(function () {   // 2. 点击触发事件
    let _this = this;
    let sUserId = $(this).parents('tr').data('id');
    let sUserName = $(this).parents('tr').data('name');

    fAlert.alertConfirm({
      title: `确定删除 ${sUserName} 这个用户信息吗？`,
      type: "error",
      confirmText: "确认删除",
      cancelText: "取消删除",
      confirmCallback: function confirmCallback() {

        $.ajax({
          url: "/admin/usersprofile/" + sUserId + "/",  // url尾部需要添加/
          // 请求方式
          type: "DELETE",
          dataType: "json",
        })
          .done(function (res) {
            if (res.errno === "0") {
              message.showSuccess("用户删除成功");
              $(_this).parents('tr').remove();
            } else {
              swal.showInputError(res.errmsg);
            }
          })
          .fail(function () {
            message.showError('服务器超时，请重试！');
          });
      }
    });
  });


  // ================== 修改用户 ================
  let $usersBtn = $("#btn-edit-user");
  $usersBtn.click(function () {
    // 判断用户信息是否修改
    // 获取修改之后的值
    let usersProfileNickname = $("input[name='nickname']").val();
    let usersProfileBorndate = $("input[name='born_time']").val();
    let usersProfileGender = $("#gender").val();
    let usersProfileMotto = window.editor.txt.html();
    console.log(usersProfileNickname,usersProfileBorndate,usersProfileGender,usersProfileMotto);
    if (noUsersProfileNickname === usersProfileNickname && noUsersProfileBorndate === usersProfileBorndate
      && noUsersProfileGender === usersProfileGender && noUsersProfileMotto === usersProfileMotto
      ) {
      message.showError('用户信息未修改！');
      return
    }

    // 获取userId
    let userId = $(this).data("user-id");
    let url = '/admin/usersprofile/' + userId + '/';
    let data = {
      "nickname": usersProfileNickname,
      "born_date": usersProfileBorndate,
      "gender": usersProfileGender,
      "motto": usersProfileMotto

    };

    $.ajax({
      // 请求地址
      url: url,
      // 请求方式
      type: 'PUT',
      data: JSON.stringify(data),
      // 请求内容的数据类型（前端发给后端的格式）
      contentType: "application/json; charset=utf-8",
      // 响应数据的格式（后端返回给前端的格式）
      dataType: "json",
    })
      .done(function (res) {
        if (res.errno === "0") {
          fAlert.alertNewsSuccessCallback("用户信息更新成功", '跳到用户管理页', function () {
            window.location.href = '/admin/usersprofile/'+userId+'/'
          })
        } else {
          fAlert.alertErrorToast(res.errmsg);
        }
      })
      .fail(function () {
        message.showError('服务器超时，请重试！');
      });

  });

  // ================== 添加用户信息 ================
  let $usersAddBtn = $("#btn-add-user");
  $usersAddBtn.click(function () {
    // 判断用户信息是否修改
    // 获取修改之后的值
    let usersProfileNickname = $("input[name='nickname']").val();
    let usersProfileBorndate = $("input[name='born_time']").val();
    let usersProfileGender = $("#gender").val();
    let usersProfileMotto = window.editor.txt.html();
    console.log(usersProfileNickname,usersProfileBorndate,usersProfileGender,usersProfileMotto);
    if (noUsersProfileNickname === usersProfileNickname && noUsersProfileBorndate === usersProfileBorndate
      && noUsersProfileGender === usersProfileGender && noUsersProfileMotto === usersProfileMotto
      ) {
      message.showError('用户信息未修改！');
      return
    }

    // 获取userId
    let userId = $(this).data("user-id");
    let url = '/admin/usersprofile/' + userId + '/';
    let data = {
      "user" :userId,
      "nickname": usersProfileNickname,
      "born_date": usersProfileBorndate,
      "gender": usersProfileGender,
      "motto": usersProfileMotto

    };

    $.ajax({
      // 请求地址
      url: url,
      // 请求方式
      type: 'POST',
      data: JSON.stringify(data),
      // 请求内容的数据类型（前端发给后端的格式）
      contentType: "application/json; charset=utf-8",
      // 响应数据的格式（后端返回给前端的格式）
      dataType: "json",
    })
      .done(function (res) {
        if (res.errno === "0") {
          fAlert.alertNewsSuccessCallback("用户信息更新成功", '跳到用户管理页', function () {
            window.location.href = '/admin/usersprofile/'+userId+'/'
          })
        } else {
          fAlert.alertErrorToast(res.errmsg);
        }
      })
      .fail(function () {
        message.showError('服务器超时，请重试！');
      });

  });

  // get cookie using jQuery
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      let cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        let cookie = jQuery.trim(cookies[i]);
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }

  // Setting the token on the AJAX request
  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      }
    }
  });

});