function markError(name, quantity, sourcekind, source, edit) {
	var filename = name.replace("/", "_") + '.json';
	var sks = sourcekind.split(',');
	var sis = source.split(',');
	var sourcestring = '';
	for (i = 0; i < sks.length; i++) {
		sourcestring +=
			'\t\t\t{\n' +
			'\t\t\t\t"value":"' + sis[i] + '",\n' +
			'\t\t\t\t"kind":"' + sks[i] + '",\n' +
			'\t\t\t\t"extra":"' + quantity + '"\n' +
			'\t\t\t}' + ((i == sks.length - 1) ? '' : ',') + '\n';
	}
	var codemessage = '';
	if (edit === "true") {
		codemessage += '### IMPORTANT: A FILE FOR THIS EVENT ALREADY EXISTS IN THE REPOSITORY.\n';
		codemessage += '### Due to limitations of the GitHub URL interface, you must copy the contents\n';
		codemessage += '### of this file into the existing JSON file for this event in order to edit it\n';
		codemessage += '### The location of the file to paste into is located at:\n';
		codemessage += '### https://github.com/astrocatalogs/sne-internal/edit/master/' + encodeURIComponent(filename) + '\n';
		codemessage += '### COMMITTING THE FILE ON THIS PAGE WILL RESULT IN A "FILE ALREADY EXISTS" ERROR.\n';
		codemessage += '### Delete all lines preceded by a # before committing any changes to the file\n';
		codemessage += '### located at the above URL.\n';
	} else {
		codemessage = '### DELETE THIS LINE TO ENABLE COMMIT BUTTON\n';
	}
	var value = encodeURIComponent(
		codemessage +
		'{\n' +
		'\t"' + name + '":{\n' + 
		'\t\t"name":"' + name + '",\n' +
		'\t\t"errors":[\n' +
		sourcestring +
		'\t\t]\n' +
		'\t}\n' +
		'}');
	var instructions = encodeURIComponent(name + '\'s ' + quantity + ' from ' + source + ' marked as being erroneous.');
	var win = window.open('https://github.com/astrocatalogs/sne-internal/new/master/?filename=' +
		encodeURIComponent(filename) + '&value=' + value + '&message=' + instructions, '_blank');
	win.focus();
}
