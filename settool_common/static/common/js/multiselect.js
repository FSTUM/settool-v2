function addLink(parent, label, callback) {
    let a = document.createElement('a');
    a.href = '#';
    a.text = label;
    $(a).click(callback);
    $(a).insertAfter(parent);
}

let defaultCallback = function (action) {
    return function () {
        $(this).parent()
            .find('select[multiple]')
            .multiSelect(action);
        return false;
    };
};

let valueCallback = function (action, value) {
    return function () {
        let elements = $(this).parent()
            .find('select[multiple]')
            .find('option')
            .map(function (idx, option) {
                if ($(option)
                    .text()
                    .toLowerCase()
                    .includes(value)) {
                    return option.value;
                }
            });

        $(this).parent()
            .find('select[multiple]')
            .multiSelect(action, elements);
        return false;
    };
};