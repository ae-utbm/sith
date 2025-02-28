document.addEventListener("DOMContentLoaded", () => {
  console.clear();
  let bandw;
  let addWeekAb = false;

  const indexNomCours = 1;
  const indexLettreGroupe = indexNomCours + 1;
  const indexTypeCours = indexLettreGroupe + 1;
  const indexGroupeCours = indexTypeCours + 1;
  const indexSemaineCours = indexGroupeCours + 1;
  const indexJourCours = indexSemaineCours + 1;
  const indexHeureDebut = indexJourCours + 1;
  const indexMinuteDebut = indexHeureDebut + 1;
  const indexHeureFin = indexMinuteDebut + 1;
  const indexMinuteFin = indexHeureFin + 1;
  const indexFreqCours = indexMinuteFin + 1;
  const indexLieuCours = indexFreqCours + 1;
  const indexSallesCours = indexLieuCours + 1;

  const listeCouleursCours = {};
  const colours = [
    "#27ae60",
    "#2980b9",
    "#c0392b",
    "#7f8c8d",
    "#f1c40f",
    "#1abc9c",
    "#95a5a6",
    "#26C6DA",
    "#C2185B",
    "#E64A19",
    "#1B5E20",
  ];
  let colourIndex = 0;

  function rand(min, max) {
    return Math.floor(Math.random() * (max - min + 1) + min);
  }

  function duree(h1, m1, h2, m2) {
    // pars ints
    h1 = Number.parseInt(h1);
    m1 = Number.parseInt(m1);
    h2 = Number.parseInt(h2);
    m2 = Number.parseInt(m2);

    // transform durations with decimal
    const decimalStart = h1 + m1 / 60;
    const decimalEnd = h2 + m2 / 60;

    const decimalDuration = decimalEnd - decimalStart;

    return decimalDuration / 0.25;
  }
  function cour(matches, periodes, jours, heuremin) {
    const timebefore = duree(
      heuremin[0],
      heuremin[1],
      matches[indexHeureDebut],
      matches[indexMinuteDebut],
    );
    const jour = jours.indexOf(matches[indexJourCours]);
    const periode = duree(
      matches[indexHeureDebut],
      matches[indexMinuteDebut],
      matches[indexHeureFin],
      matches[indexMinuteFin],
    );
    const frequency = matches[indexFreqCours];
    let groupe = matches[indexGroupeCours];
    const type = matches[indexTypeCours];
    const groupecours = matches[indexLettreGroupe] || "";

    // define left offset
    let left = (jour / jours.length) * 100;
    let semaine = "";
    if (frequency === "2" || frequency === "B") {
      semaine = matches[indexSemaineCours]
        ? "<br>semaine " + matches[indexSemaineCours]
        : "";
    }
    // console.log(semaine)

    //if same course at same hour, increase left offset
    const lasthour = $("#edt > div:last").attr("alt");
    const lastday = $("#edt > div:last").attr("data-jour");
    const lastroom = $("#edt > div:last").attr("data-salle");
    const lastFreq = $("#edt > div:last").attr("data-frequence");
    console.log(lastFreq, matches[indexNomCours], matches[indexTypeCours]);
    let half = 1;
    if (lasthour !== undefined) {
      // fix bug cours meme heure meme salle mais frequence 1
      // fix bug cours meme heure frequence 1 mais distanciel : enlever check room
      if (
        lasthour == matches[indexHeureDebut] &&
        lastday == matches[indexJourCours] &&
        matches[indexFreqCours] == 1 &&
        lastFreq == 1
      ) {
        console.log("freq 1 bug", matches);
        half = 0.5;
        $("#edt > div:last")[0].style.width =
          Number.parseInt($("#edt > div:last")[0].style.width) / 2 + "%";
        left += (1 / 2 / jours.length) * 100;
      }
    }
    if (!groupe) {
      groupe = matches[indexGroupeCours];
    }
    const fin = (periode / periodes) * 100 + (timebefore / periodes) * 100 + "%";
    const horaire = `${matches[indexHeureDebut]}h${matches[indexMinuteDebut]} — ${matches[indexHeureFin]}h${matches[indexMinuteFin]}`;
    const lieu =
      (matches[indexLieuCours] || "") +
      (matches[indexLieuCours] && matches[indexSallesCours] ? " — " : "") +
      (matches[indexSallesCours] || "");

    $("#edt").append(
      '<div class="cour middle" alt="' +
        matches[indexHeureDebut] +
        '"><span class="groupe">' +
        type +
        "</span><div>" +
        matches[indexNomCours] +
        " (groupe de " +
        type +
        " " +
        matches[indexGroupeCours] +
        ")" +
        semaine +
        "<br>" +
        horaire +
        "<br>" +
        lieu +
        '</div><span class="taille"></span></div>',
    );

    const cours = $("#edt > div:last")[0];
    // mettre tous les attibuts
    cours.setAttribute("data-fin", fin);
    cours.setAttribute("data-jour", matches[indexJourCours]);
    cours.setAttribute("data-frequence", matches[indexFreqCours]);

    if (matches[indexFreqCours] === "2") {
      // recuperer cours precedent a celui juste ajouté
      const prevCours = $("#edt > div:last").prev();
      console.log(matches, prevCours.attr("data-frequence"));
      const prevJour = prevCours.attr("data-jour");
      const prevfin = prevCours.attr("data-fin");
      console.info(
        prevJour,
        matches[indexJourCours],
        Number.parseFloat(prevfin),
        (timebefore / periodes) * 100,
        prevJour == matches[indexJourCours],
        Number.parseFloat(prevfin) >= (timebefore / periodes) * 100,
      );
      // si c'est le même jour
      // si l'heure du fin du précédent est plus grand à mon heure de départ
      if (
        prevJour == matches[indexJourCours] &&
        Number.parseFloat(prevfin) >= (timebefore / periodes) * 100
      ) {
        console.info("moving left for", matches);
        left += ((1 / jours.length) * 100) / matches[indexFreqCours];
      }
    }
    $("#edt > div:last").css({
      height: (periode / periodes) * 100 + "%",
      width: (((half * 1) / jours.length) * 100) / frequency + "%",
      position: "absolute",
      left: left + "%",
      top: (timebefore / periodes) * 100 + "%",
      background: bandw ? "white" : listeCouleursCours[matches[indexNomCours]],
      "border-color": bandw
        ? listeCouleursCours[matches[indexNomCours]]
        : "transparent",
      color: bandw ? "black" : "inherit",
    });
  }

  function entete(jours) {
    for (let u = 0; u < jours.length; u++) {
      $("#entete").append("<div>" + jours[u] + "</div>");
      $("#entete div:last").css("width", (1 / jours.length) * 100 + "%");
    }
  }

  function horaires(heuremin, heuremax, periodes) {
    const heurestart = heuremin[0];

    const heureend = heuremax[0];

    let heures = heureend - heurestart;
    heures++;
    for (let b = 0; b < heures; b++) {
      const heure = heurestart + b;
      const top = (duree(heuremin[0], heuremin[1], heure, 0) / periodes) * 100;
      $("#heures").append('<div class="heure">' + heure + ":00<div></div></div>");
      $("#heures > div:last").css("top", top + "%");
    }
  }
  function saveAs(uri, filename) {
    const link = document.createElement("a");
    if (typeof link.download === "string") {
      link.href = uri;
      link.download = filename;

      //Firefox requires the link to be in the body
      document.body.appendChild(link);

      //simulate click
      link.click();

      //remove the link when done
      document.body.removeChild(link);
    } else {
      window.open(uri);
    }
  }

  function edt() {
    //reinit div
    $("body").css("overflow", "auto");
    $("#heures").html("");
    $("#entete").html("");
    $("#edt").find(".cour").remove();

    $("form").hide();
    //get value
    const textarea = $("form textarea").val();
    const cours = textarea.trim().split("\n");

    bandw = $("#bandw:checked").length;
    addWeekAb = $("#weekab:checked").length;

    const jours = [];
    const heuremin = [20, 20];
    const heuremax = [0, 0];

    const reg =
      /([A-Z0-9]+|[A-Z0-9]+\+[A-Z0-9]+)\s+([A-Z]+)?\s*([A-Z]{2})\s*([0-9]+)\s+([A-Z]?)\s*([a-z]+)\s+([0-9]+)[:h]([0-9]{2})\s+([0-9]+)[:h]([0-9]{2})\s+([0-9A-B])\s+([A-Za-zé]{2,})?\s*(([A-Z]\s?[A-Za-z0-9]+[a-zA-Z]?)(, )?(([A-Z]\s?[0-9]+[a-zA-Z]?)|[a-zA-Z]+)?|[a-zA-Z0-9]+)?/;
    for (let i = 0; i < cours.length; i++) {
      const matches = reg.exec(cours[i]);

      if (!matches) {
        $("form").show();
        alert("Ton emploi du temps ne respecte pas le format inscris dans l'exemple.");
        return;
      }
      const jour = matches[indexJourCours];
      if (jours.indexOf(jour) === -1) {
        jours.push(jour);
      }

      if (bandw) {
        $("#edt").addClass("impression");
      }

      //couleur de cours
      if (listeCouleursCours[matches[indexNomCours]] === undefined) {
        if (bandw) {
          r = g = b = rand(65, 255);
          listeCouleursCours[matches[indexNomCours]] =
            "rgb(" + r + ", " + g + ", " + b + ")";
        } else {
          listeCouleursCours[matches[indexNomCours]] = colours[colourIndex];
          colourIndex = (colourIndex + 1) % colours.length;
        }
      }

      // heure min
      const heuredebut = Number.parseInt(matches[indexHeureDebut]);
      const minutedebut = Number.parseInt(matches[indexMinuteDebut]);
      // console.log(heuredebut, minutedebut);
      if (heuredebut < heuremin[0]) {
        heuremin[0] = heuredebut;
        heuremin[1] = minutedebut;
      }
      if (heuredebut == heuremin[0] && minutedebut < heuremin[1]) {
        heuremin[1] = minutedebut;
      }

      // heure max
      const heurefin = Number.parseInt(matches[indexHeureFin]);
      const minutefin = Number.parseInt(matches[indexMinuteFin]);
      if (heurefin > heuremax[0]) {
        heuremax[0] = heurefin;
        heuremax[1] = minutefin;
      }
      if (heurefin == heuremax[0] && minutefin > heuremax[1]) {
        heuremax[1] = minutefin;
      }
    }

    // calcul periodes max de 15min de travail
    const periodes = duree(heuremin[0], heuremin[1], heuremax[0], heuremax[1]);

    //calculs des periodes de chaque cours
    for (let a = 0; a < cours.length; a++) {
      const matches = reg.exec(cours[a]);
      cour(matches, periodes, jours, heuremin);
    }
    entete(jours);
    horaires(heuremin, heuremax, periodes);

    if (document.getElementById("non").checked == false) {
      html2canvas(document.getElementById("container"), {
        onrendered: (canvas) => {
          if (document.getElementById("png").checked) {
            saveAs(canvas.toDataURL(), "edt" + (bandw ? "-impression" : "") + ".png");
          } else {
            const imgData = canvas.toDataURL("image/jpeg", 1);
            const pdf = new jsPDF({
              orientation: "landscape",
              unit: "mm",
              format: "a4",
            });
            const pageWidth = pdf.internal.pageSize.getWidth();
            const pageHeight = pdf.internal.pageSize.getHeight();
            const imageWidth = canvas.width;
            const imageHeight = canvas.height;

            const ratio =
              imageWidth / imageHeight >= pageWidth / pageHeight
                ? pageWidth / imageWidth
                : pageHeight / imageHeight;
            //pdf = new jsPDF(this.state.orientation, undefined, format);
            pdf.addImage(
              imgData,
              "JPEG",
              0,
              0,
              imageWidth * ratio,
              imageHeight * ratio,
            );
            pdf.save("edt" + (bandw ? "-impression" : "") + ".pdf");
          }
        },
      });
    }
  }

  $("body > form").on("submit", (e) => {
    e.preventDefault();
    edt();
  });
});
