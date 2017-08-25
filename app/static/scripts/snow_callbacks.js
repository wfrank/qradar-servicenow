function create_servicenow_incident_preview_dialog() {
    dojo.require("dijit.Dialog");
    dojo.require("dojox.layout.TableContainer");

    var existing = dijit.registry.byId("servicenow_incident_preview_dialog");
    if (existing) {
        existing.destroyRecursive(true);
    }

    var dialog = dijit.Dialog({
        id: "servicenow_incident_preview_dialog",
        title: "Preview ServiceNow Incident",
        baseClass: "soria oneui",
        style: "background-color: white; border-radius: 4px; border: 4px solid rgba(3,3,3,0.4);",
        execute: servicenow_submit_incident,
        onKeyDown: function(event) { event.stopPropagation(); return true; }
    });

    return dialog;
}


$(document).ready(function () {
    /* Subscribe for selection changes on the offenses table */
    if (typeof defaultTable !== 'undefined') {
        // only applicable on summary screen, not detail screen
        domapi.addEvent(defaultTable, "selectionchanged", servicenow_app_toolbar_enable);
    }

    create_servicenow_incident_preview_dialog()
});


$(window).bind("toolbarLoaded", servicenow_app_toolbar_enable);

function servicenow_app_toolbar_enable() {
    /* Enable the servicenow button if a single offense is selected */
    var isOK = ( pageId == "OffenseSummary" ) || ( selectedRows.length == 1 );
    setActionEnabled("servicenow_app_click_incident_toolbar_button", isOK);
}


function servicenow_app_click_incident_toolbar_button() {
    /* Called when the user clicks the servicenow toolbar button */
    var offense_id;

    if (pageId === "OffenseList" || pageId === "MyOffenseList") {
        // Source is the offense list
        var selectedRows = QRadar.getSelectedRows()
        if (selectedRows.length === 0) {
            alert("Select an offense please.");
            return;
        }
        else if (selectedRows.length > 1) {
            alert("Select a single offense please.");
            return;
        }
        offense_id = selectedRows[0];
    } else {
        // Source is the offense details page
        offense_id = QRadar.getItemId();
    }

    var content_url = QRadar.getApplicationBaseUrl() + "/preview/" + offense_id;

    var dialog = dijit.registry.byId("servicenow_incident_preview_dialog");

    dialog.set("href", content_url);
    dialog.set("offense_id", offense_id);

    dialog.show();
}


function servicenow_show_result(result) {
        var msg;
        if (!result)
                msg = "No result found for action";

        if (result.hasOwnProperty("error") && result.error && result.error != "") {
                msg = result.error;
        } else if (result.hasOwnProperty("isException") && result.isException) {
                msg = "An error occurred processing offense.";
                if (result.hasOwnProperty("message") && result.message && result.message != "") {
                        msg += "\nError message: " + result.message;
                }
        } else if (result.hasOwnProperty("record") && result.record && result.record != "") {
                msg = "ServiceNow incident record has been created";
                msg += "\n\nIncident ID: " + result.record;
                if (result.hasOwnProperty("url") && result.url && result.url != "") {
                        msg += "\nIncident URL: " + result.url;
                }
        } else {
                msg = "Unknown error occurred. Raw result is: ";
                msg += JSON.stringify(result);
        }

        alert(msg);
}


function servicenow_submit_incident(updates) {

    var dialog = dijit.registry.byId("servicenow_incident_preview_dialog");
    var offense_id = dialog.get("offense_id");

    var args = {
        httpMethod: "POST",
        path: "/application/submit/" + offense_id,
        contentType: "application/json",
        body: JSON.stringify(updates),
        onComplete: function () {
            var result = JSON.parse(this.responseText);
            servicenow_show_result(result);
        },
        onError: function () {
            alert("Problem sending request to QRadar: " + this.responseText);
        }
    };

    QRadar.rest(args);
}
