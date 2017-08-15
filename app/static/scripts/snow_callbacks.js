$(function() {
	$("[name*='Create ServiceNow Security Event']").hide();
	$("[name*='Create ServiceNow Security Incident']").hide();
	servicenow_qradar_handleBtnConfig()
});

function servicenow_qradar_handleResponse(result, type) {
	var msg;
	if (!result)
		msg = "No result found for action";
	if (result.hasOwnProperty("url") && result.url && result.url != "") {
		msg = type + " record has been created in ServiceNow";
		msg += "\n\nRecord URL: " + result.url;
	} else if (result.hasOwnProperty("error") && result.error && result.error != "")
		msg = result.error;
	else if (result.hasOwnProperty("isException")
		&& result.isException) {
		msg = "An error occurred processing offense.";
		if (result.hasOwnProperty("message") && result.message && result.message != "") {
			msg += "\nError message: " + result.message;
		}
	} else {
		msg = "Unknown error occurred. Raw result is: ";
		msg += JSON.stringify(result);
	}

	alert(msg);
}

function servicenow_qradar_createSICallback(result) {
	servicenow_qradar_handleResponse(result, "Security Incident");
}

function servicenow_qradar_createEvtCallback(result) {
	servicenow_qradar_handleResponse(result, "Security Event");
}

function servicenow_qradar_handleBtnConfig(){
	var cookies = document.cookie;
	if (!cookies)
		return;
	cookies = cookies.trim();
	if (cookies.length == 0)
		return;

	cookies = cookies.split(";");
	var csrf = null;
	for (var i = 0; i < cookies.length; i++) {
		if (cookies[i].length == 0)
			continue;
		var cookieParts = cookies[i].split("=");
		if (cookieParts.length == 2 && cookieParts[0].trim() == "QRadarCSRF") {
			csrf = cookieParts[1].trim();
			break;
		}
	}

	if (!csrf)
		return;

	applicationMethod = applicationMethod || function() {};
	$.ajax({
		url: "/api/gui_app_framework/applications",
		type: "GET",
		beforeSend: function(xhr){
			xhr.setRequestHeader('QRadarCSRF', csrf);
		}
	}).done(function(data) {
		if (!data)
			return;

		var appId = null;
		for (var idx = 0; idx < data.length; idx++) {
			var app = data[idx];
			if (!app || !app.manifest || !app.manifest.name || !app.manifest.app_id)
				continue;
			if (app.manifest.name == 'ServiceNow Integration')
				appId = app.manifest.app_id;
		}
		if (!appId || appId.length == 0)
			return;

		applicationMethod( appId, "getSNButtonConfig", {"context": ""}, null,
			function(resultJSON) {
				var showEvent = false;
				if ('show_event' in resultJSON) {
					showEvent = resultJSON.show_event;
				}
				$("[name*='Create ServiceNow Security Event']").toggle(showEvent);

				var showIncident = false;
				if ('show_incident' in resultJSON) {
					showIncident = resultJSON.show_incident;
				}
				$("[name*='Create ServiceNow Security Incident']").toggle(showIncident);
			}
		);
	});
}