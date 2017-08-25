$j( document ).ready(function(){
	$j('btn').off();
	$j('#btn_reset').click(function() {
		location.reload();
		window.scrollTo(0, 0);
	});

	$j('.btn.remove_mapping').click(function(){
		$j(this).parents('.form-group').detach();
	});

	var addMapping = function(context, sectionIdSel, mapPrefix) {
		var currentCount = $j(sectionIdSel + ' > .form-group').length;
		var idKey = mapPrefix + 'key.' + currentCount;
		var idVal = mapPrefix + 'value.' + currentCount;
		var $cln = $j('#mapping_tpl > .form-group').clone(true, true);
		$cln.find(".key").attr({
			id: idKey,
			name: idKey
		});
		$cln.find(".val").attr({
			id: idVal,
			name: idVal
		});
		$j(context).prev('.form-group').after($cln);
	};

	$j('#offense_mappings > .add_mapping').click(function(){
		addMapping(this, "#offense_mappings", "offense_map.");
	});

	$j('#vulnerability_mappings > .add_mapping').click(function(){
		addMapping(this, "#vulnerability_mappings", "vulnerability_map.");
	});

	$j('#group_mappings > .add_mapping').click(function(){
		addMapping(this, "#group_mappings", "group_map.");
	});

	$j('.sn-popover').each(function() {
		var target = $j(this).attr('data-target-tpl');
		var content = $j("#" + target).html();
		$j(this).click(function(event){
			event.preventDefault();
		});
		$j(this).popover({
			content: content,
			html: true,
			trigger: 'focus',
			container: 'body'
		});
	});
});