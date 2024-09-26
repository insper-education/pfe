function bars() {
    var myLinks = document.getElementById("myLinks");
    if (myLinks.style.display === "block") {
        myLinks.style.display = "none";
    } else {
        myLinks.style.display = "block";
    }
}

// Add event listener for the Escape key
document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") {
        var myLinks = document.getElementById("myLinks");
        if (myLinks.style.display === "block") {
            myLinks.style.display = "none";
        }
    }
});