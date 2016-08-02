<script>
    var error_class = 'has-error'

    function required(data){
    	if (data.trim().length != 0){
    		return true;
    	}else{
    		return '此字段为必填字段';
    	}
    }

    function email(data){
        var re = /^.+@[^.].*\.[a-z]{2,10}$/;
        if (re.test(data)){
        	return true;
        }else{
        	return '邮箱格式不正确';
        }
    }

    function file(data){
    	var re = /^[A-Za-z0-9_\./\-]*$/;
    	if (re.test(data)){
        	return true;
        }else{
        	return '文件列表格式不正确';
        }
    }

    function version(data){
    	var re = /^[A-Za-z0-9_\./\-@]*$/;
    	if (re.test(data)){
        	return true;
        }else{
        	return '版本号信息不正确';
        }
    }

    function pre_check(tag){
    	var data = $("#" + tag)
    	if (data.prop('checked')){
        	return true;
        }else{
        	return false;
        }
    }

    function validate_datium(data,functions){
        for(var func in functions){
            var retval = functions[func](data)
            if (typeof(retval) == 'boolean'){
    		    continue;
    		}else{
    		    throw retval;
    		}
    	}
    }

    function validate_data(data, functions, split){
        var split = arguments[2] ? arguments[2] : '';
        if (! split){
            validate_datium(data,functions)
        }else{
            if (data){
                data_list = data.split(split);
                for (var datium in data_list) {
                    if (data_list[datium]) {
                        validate_datium(data_list[datium], functions)
                    }
                }
            }
            else{
                validate_datium(data, functions)
            }
        }
    	return true;
    }

    function validate_pre(data, functions, split, pre){
        var pre = arguments[3] ? arguments[3] : '';
        if(pre){
            if(pre[0][0](pre[0][1])){
                validate_data(data, functions, split);
            }
        }else{
            validate_data(data, functions, split);
        }
    }
    function sign(tag){
        var data = $("#" + tag);
        data.click(function() {
            var error = $("#" + tag + "_error");
            if (error[0]){
                error.remove();
                data.parent().removeClass(error_class);
            }
        })
    }

    function validate(tag, funcs, split, pre, outter){
        var data = $("#" + tag);
        try{
            validate_pre(data.val(),funcs,split,pre);
        }catch(err){
            data.parent().addClass(error_class);
            if ($("#" + tag + "_error")[0]){;
                $("#" + tag + "_error").text(err);
            }else{
                console.log(outter)
                if (outter === 0) {
                    data.parent().after($("<p id='" + tag + "_error' class='help-block' style='color: #a94442'></p>").text(err));
                }else{
                    data.after($("<p id='" + tag + "_error' class='help-block'></p>").text(err));
                }
            }
        	return false;
        }
        return true
    }

    function validate_form(){
        results = [validate('event_email_title', [required]), validate('event_email_receiver',
                  [required, email], ';'), validate('event_file_list', [required, file], '\n'), validate('event_version_number',
                  [version], '\n'), validate('db_file_list', [required, file], '\n', [[pre_check,'db_online_yes']]), validate('event_etime', [required], 0, 0, 0)]
        for(var x in results){
            if (results[x]){
                continue;
            }else{
                return false;
            }
        }
        return true;
    }

    sign('event_email_title');
    sign('event_email_receiver');
    sign('event_file_list');
    sign('event_version_number');
    sign('db_file_list');
    sign('event_etime');

</script>
