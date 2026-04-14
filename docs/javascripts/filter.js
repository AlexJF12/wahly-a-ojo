/* Client-side course filtering for the homepage card grid. */

document.addEventListener("DOMContentLoaded", function () {
  var pills = document.querySelectorAll(".filter-pill");
  var cards = document.querySelectorAll(".recipe-card");

  if (!pills.length) return;

  pills.forEach(function (pill) {
    pill.addEventListener("click", function () {
      var filter = pill.dataset.filter;

      pills.forEach(function (p) { p.classList.remove("active"); });
      pill.classList.add("active");

      cards.forEach(function (card) {
        var match = filter === "all" || card.dataset.course === filter;
        card.classList.toggle("hidden", !match);
      });
    });
  });
});
