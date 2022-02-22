/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
odoo.define('otp_auth.wk_otp_login', function (require) {
    "use strict";
    
const ajax = require('web.ajax');
    $(document).ready(function() {
        if ($('#otplogincounter').get(0)) {
            $(".control-button").hide();
            $(".control-button").attr("disabled", true);
//            $(".field-password").hide();
//            $( ".oe_login_form" ).wrapInner( "<div class='container' id='wk_container'></div>");
//            $(".field-login").before("<i class='fa fa-arrow-left text-primary wk_back_btn' ></i>");
//            $(".wk_back_btn").hide();
//            $("#password").addClass('wkpassword');
        }
        $('.wk_next_btn').on('click', function(e) {
            debugger;
            if ($(".field-otp-option").css("display") == 'none') {
                $(".field-login").hide();
                $(".wk_back_btn").show();
                $(".field-otp-option").css("display","");
            } else {
//                var radioVal = $('input[name=radio-otp]:checked').val();
                var radioVal = 'radiotp';
                if (radioVal == 'radiotp') {
                    generateLoginOtp();
                } else if (radioVal == 'radiopwd') {
                    $(".field-password").show();
                    $("#password").attr('placeholder', 'Enter Password');
                    $(".control-button").show();
                    $(".wk_next_btn").hide();
                    debugger;
                    $(":submit").show();
                    $(":submit").attr("disabled", false);
                    $(".field-otp-option").css("display","none");
                }
            }
        });


        $('.wk_back_btn').on('click', function(e) {
            $('#wk_error').remove();
            $('.wk_login_resend').remove();
            if ($(".field-otp-option").css("display") != 'none') {
                $(".field-login").show();
                $(".wk_back_btn").hide();
                $(".field-otp-option").css("display","none");
            } else if ($(".field-otp-option").css("display") == 'none') {
                $(".field-otp-option").css("display","");
                $(".field-password").hide();
                $(".control-button").hide();
                $(".wk_next_btn").show();
            }
        });
        if ($('.oe_login_form').length) {
            debugger;
//            $('label[for=password], input#password').text("OTP");
            $(".field-mobile").hide();
            $(".field-country").hide();
            debugger;
            $(":submit").attr("disabled", true);
            $(":submit").hide();
        }
        $('input:radio[name="radio-otp"]').change(function() {
            if ($(this).val() == 'radiotp') {
                $('label[for=password], input#password').text("OTP");
            } else if ($(this).val() == 'radiopwd') {
                $('label[for=password], input#password').text("Password");
            }
        });

        $(this).on('click', '.wk_login_resend', function(e) {
            generateLoginOtp();
        });
        $('label[for="password"]').show();
        // $('.wkpassword').focusin(function () {
        //     $('label[for="password"]').show();
        // });
        // $('.wkpassword').focusout(function () {
        //     $('label[for="password"]').hide();
        // });

    });

    function generateLoginOtp() {
        debugger;
        var mobile = $('#mobile').val();
        var email = $('#login').val();
        var password = $('#password').val();
        var otp_type = $('.otp_type').val();
        debugger;
        $("div#wk_loader").addClass('show');
            ajax.jsonRpc("/send/otp", 'call', {'email':email, "loginOTP":'loginOTP', 'mobile':mobile, 'password':password})
                .then(function (data) {
                    if (data) {
                        if (data == 3){
                            debugger;
                            $(".control-button").show();
                            $(".control-button").attr("disabled", false);
                            document.getElementsByTagName("form")[0].submit();
                        }
                        if (data.email) {
                            debugger;
                            if (data.email.status == 1) {
                                debugger;
                                $("div#wk_loader").removeClass('show');
                                $('#wk_error').remove();
                                getLoginInterval(data.email.otp_time);
                                $(".field-password").show();
                                $(".field-login").hide();
                                $("#password").attr('placeholder', 'Enter OTP');
                                $("#password").attr("type", "text");
                                $("#password").val('');
                                if (otp_type == '4') {
                                    $("#password").attr("type", "text");
                                }
                                debugger;
                                $('label[for=password], input#password').text("OTP");
                                $(".field-password").after("<p id='wk_error' class='alert alert-success'>" +data.email.message + "</p>");
                                $(".control-button").show();
                                $(".control-button").attr("disabled", false);
                                $(".wk_next_btn").hide();
                                debugger;
                                $(":submit").show();
                                $(":submit").attr("disabled", false);
                                $(".field-otp-option").css("display","none");
                            } else {
                                $("div#wk_loader").removeClass('show');
                                $('#wk_error').remove();
                                $(".field-otp-option").after("<p id='wk_error' class='alert alert-danger'>" +data.email.message + "</p>");
                                $(".field-password").after("<p id='wk_error' class='alert alert-success'>" + data.email.message + "</p>");
                            }
                        }
                        if (data.mobile) {
                            if (data.mobile.status == 1) {
                                // if (data.mobile.status) {
                                //     $('label[for=login], input#login').val(data[3]);
                                // }

                                if (data.email.status != 1) {
                                    $("div#wk_loader").removeClass('show');
                                    $('#wk_error').remove();
                                    getLoginInterval(data.email.otp_time);
                                    $(".field-password").show();
                                    $("#passwogenerateSMSSignUpOtprd").attr('placeholder', 'Enter OTP');
                                    if (otp_type == '4') {
                                        $("#password").attr("type", "text");
                                    }
                                    $(".control-button").show();
                                    $(".wk_next_btn").hide();
                                    $(":sumbit").show();
                                    $(".field-otp-option").css("display","none");
                                }
                                $(".field-password").after("<p id='wk_error' class='alert alert-success'>" +data.mobile.message + "</p>");
                            } else {
                                if (data.email.status != 1) {
                                    $("div#wk_loader").removeClass('show');
                                    $('#wk_error').remove();
                                }
                                $(".field-otp-option").after("<p id='wk_error' class='alert alert-danger'>" +data.mobile.message + "</p>");
                            }
                        }
                    }
                }).guardedCatch(function (error){
                    console.log(error)
                });
        // }
    }

    function getLoginInterval(otpTimeLimit) {
        var countDown = otpTimeLimit;
        var x = setInterval(function() {
            countDown = countDown - 1;
            $("#otplogincounter").html("OTP will expire in " + countDown + " seconds.");
            if (countDown < 0) {
                clearInterval(x);
                $('#wk_error').remove();
                $("#otplogincounter").html("<br/><a class='btn btn-link pull-right wk_login_resend' href='#'>Resend OTP</a>");
            }
        }, 1000);
    }

})