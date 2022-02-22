/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
odoo.define('otp_auth.wk_otp', function (require) {
    "use strict";
    
    var ajax = require('web.ajax');
    $(document).ready(function() {
        debugger;
        if ($('#otpcounter').get(0)) {
            $("#otpcounter").html("<a class='btn btn-link pull-left wk_send' href='#'>Send OTP</a>");
            debugger;
            $(":submit").attr("disabled", true);
            $("#otp").css("display","none");
            $( ".oe_signup_form" ).wrapInner( "<div class='container' id='wk_container'></div>");
        }

        var change_count=0
        
        $(document).on('change','#login',function(){
        debugger;
            if(change_count!=0){
                window.clearInterval(window.myInterval); 
                getInterval(0);    
                // $("#otpcounter").html("<a class='btn btn-link  wk_resend' href='#'>Resend OTP</a>");
                $('#wk_error').remove();
                $('.oe_login_buttons button[type=submit]').attr('disabled','disabled');
            }
            else{
                change_count =1
            }

        });
        
        $('.wk_send').on('click', function(e) {
            var email = $('#login').val();
            if (email) {
                if(validateEmail(email)) {
                    generateOtp();
                } else {
                    $('#wk_error').remove();
                    $(".field-confirm_password").after("<p id='wk_error' class='alert alert-danger'>Please enter a valid email address.</p>");
                }
            } else {
                $('#wk_error').remove();
                $(".field-confirm_password").after("<p id='wk_error' class='alert alert-danger'>Please enter an email address.</p>");
            }
        });
        $(this).on('click', '.wk_resend', function(e) {
            $(".wkcheck").remove();
            generateOtp();
        });
        verifyOtp();
    });

    function validateEmail(emailId) {
        var mailRegex = /^([\w-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([\w-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$/;
        return mailRegex.test(emailId);
    };

    function getInterval(otpTimeLimit) {
        var countDown = otpTimeLimit;
        window.myInterval = setInterval(function() {
            countDown = countDown - 1;
            $("#otpcounter").html("OTP will expire in " + countDown + " seconds.");            
            if (countDown < 0) {
                window.clearInterval(window.myInterval);
                $("#otpcounter").html("<a class='btn btn-link  wk_resend' href='#'>Resend OTP</a>");
            }
        }, 1000);
    }

    function generateOtp() {
        var email = $('#login').val();
        var mobile = $('#mobile').val();
        var userName = $('#name').val();
        var country_id = $('#country_id').val();
        debugger;
        $("div#wk_loader").addClass('show');
        $('#wk_error').remove();
        $('.alert.alert-danger').remove();
        ajax.jsonRpc("/generate/otp", 'call', {'email':email, 'userName':userName, 'mobile':mobile, 'country':country_id})
            .then(function (data) {
                if (data[0] == 1) {
                    $("div#wk_loader").removeClass('show');
                    $('.wk_send').addClass('d-none');
                    getInterval(data[2]);
                    $("#wkotp").after("<p id='wk_error' class='alert alert-success'>" +data[1] + "</p>");
                    $("#otp").css("display","");
                    $('#otp').after($('#otpcounter'));
                } else {
                    $("div#wk_loader").removeClass('show');
                    $('#wk_error').remove();
                    $(".field-confirm_password").after("<p id='wk_error' class='alert alert-danger'>" +data[1] + "</p>");
                }
            }).fail(function (error){
                console.log(error)
            });
    }

    function verifyOtp() {
        $('#otp').bind('input propertychange', function() {
            if ($(this).val().length == 6) {
                var otp = $(this).val();
                var email = $('#login').val();
                ajax.jsonRpc("/verify/otp", 'call', {'email':email,'otp':otp})
                    .then(function (data) {
                        if (data) {
                            $('#otp').after("<i class='fa fa-check-circle wkcheck' aria-hidden='true'></i>");
                            $(".wkcheck").css("color","#3c763d");
                            $('#wkotp').removeClass("form-group has-error");
                            $('#wkotp').addClass("form-group has-success");
                            $(":submit").removeAttr("disabled");
                        } else {
                            debugger;
                            $(":submit").attr("disabled", true);
                            $('#otp').after("<i class='fa fa-times-circle wkcheck' aria-hidden='true'></i>");
                            $('#wkotp').removeClass("form-group has-success");
                            $(".wkcheck").css("color","#a94442");
                            $('#wkotp').addClass("form-group has-error");
                        }
                    }).fail(function (error){
                        console.log(error)
                    });
            } else {
                debugger;
                $(":submit").attr("disabled", true);
                $(".wkcheck").remove();
                $('#wkotp').removeClass("form-group has-success");
                $('#wkotp').removeClass("form-group has-error");
                $('#wkotp').addClass("form-group");
            }
        });
    }

})
