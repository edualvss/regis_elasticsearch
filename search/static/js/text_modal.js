function open_text(obj) {
  // Get the button that opens the modal
  //  var btn = document.getElementById("open_button");
  var btn = obj;

  var obj_id = obj.id.substring(6);

  // Get the modal
  var modal = document.getElementById("doc" + obj_id);

  // Get the <span> element that closes the modal
  var span = modal.getElementsByClassName("close")[0];

  // When the user clicks on the button, open the modal
  //btn.onclick = function () {
  modal.style.display = "block";
  //};

  // When the user clicks on <span> (x), close the modal
  span.onclick = function () {
    modal.style.display = "none";
  };

  // When the user clicks anywhere outside of the modal, close it
  window.onclick = function (event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  };
}
