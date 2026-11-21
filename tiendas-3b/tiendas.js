// Tiendas 3B en la CDMX. Fuente: directorio Tiendeo; posiciones verificadas con el geocodificador de Mapbox
// y ajustadas a su edificio. ancho/fondo (m) y ang salen del contorno del edificio; esc = escala del modelo para
// que quepa; rot = giro (grados, antihorario desde el este) con el frente hacia la calle.
// revisar: true = no se pudo confirmar la ubicación.
const TIENDAS = [
  {
    "id": "t646612",
    "nombre": "Tiendas 3B",
    "dir": "Av Vasco de Quiroga 1472",
    "cp": "01210",
    "coords": [
      -99.234063,
      19.383198
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 19,
    "en_calle": false,
    "huella": "ok",
    "ancho": 27.2,
    "fondo": 17.8,
    "ang": 91.3,
    "rot": 271.3,
    "esc": 2.2
  },
  {
    "id": "t646715",
    "nombre": "Tiendas 3B",
    "dir": "Av. Vasco de Quiroga",
    "cp": "01260",
    "coords": [
      -99.243218,
      19.380267
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 8,
    "en_calle": true,
    "huella": "grande",
    "ancho": 88.5,
    "fondo": 49.4,
    "ang": 16.9,
    "rot": 196.9,
    "esc": 2.2
  },
  {
    "id": "t632376",
    "nombre": "Tiendas 3B",
    "dir": "Cll Adolfo De La Huerta 30 Esq Adolfo Lopez Mateos",
    "cp": "01290",
    "coords": [
      -99.22084,
      19.377594
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 19,
    "en_calle": false,
    "huella": "ok",
    "ancho": 22.4,
    "fondo": 17.2,
    "ang": 90.8,
    "rot": 270.8,
    "esc": 2.2
  },
  {
    "id": "t646711",
    "nombre": "Tiendas 3B",
    "dir": "Agrarismo s/n",
    "cp": "02000",
    "coords": [
      -99.185733,
      19.482415
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 10,
    "en_calle": false,
    "huella": "grande",
    "ancho": 118.3,
    "fondo": 82.3,
    "ang": 79.6,
    "rot": 79.6,
    "esc": 2.2
  },
  {
    "id": "t646613",
    "nombre": "Tiendas 3B",
    "dir": "Av.de las Granjas 399",
    "cp": "02020",
    "coords": [
      -99.174425,
      19.481333
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 22,
    "en_calle": false,
    "huella": "ok",
    "ancho": 10.0,
    "fondo": 5.2,
    "ang": 171.9,
    "rot": 351.9,
    "esc": 0.85
  },
  {
    "id": "t632223",
    "nombre": "Tiendas 3B",
    "dir": "Cedros sn",
    "cp": "02240",
    "coords": [
      -99.179747,
      19.492092
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 8,
    "en_calle": true,
    "huella": "ok",
    "ancho": 15.4,
    "fondo": 5.3,
    "ang": 74.6,
    "rot": 74.6,
    "esc": 0.85
  },
  {
    "id": "t632200",
    "nombre": "Tiendas 3B",
    "dir": "Diagonal de San Antonio 1107",
    "cp": "03020",
    "coords": [
      -99.1596,
      19.393668
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 2,
    "en_calle": false,
    "huella": "grande",
    "ancho": 34.2,
    "fondo": 25.9,
    "ang": 173.8,
    "rot": 173.8,
    "esc": 2.2
  },
  {
    "id": "t646721",
    "nombre": "Tiendas 3B",
    "dir": "Porfirio Diaz s/n",
    "cp": "03100",
    "coords": [
      -99.16802,
      19.381365
    ],
    "revisar": false,
    "verif": "en edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "grande",
    "ancho": 50.5,
    "fondo": 23.5,
    "ang": 79.5,
    "rot": 79.5,
    "esc": 2.2
  },
  {
    "id": "t646723",
    "nombre": "Tiendas 3B",
    "dir": "Av. Miguel Hidalgo No.27",
    "cp": "03400",
    "coords": [
      -99.15246,
      19.351456
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 13,
    "en_calle": false,
    "huella": "ok",
    "ancho": 12.1,
    "fondo": 7.0,
    "ang": 82.6,
    "rot": 82.6,
    "esc": 1.13
  },
  {
    "id": "t646704",
    "nombre": "Tiendas 3B",
    "dir": "Avenida Division del Norte No.2683",
    "cp": "04120",
    "coords": [
      -99.15182,
      19.352266
    ],
    "revisar": false,
    "verif": "en edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "grande",
    "ancho": 69.1,
    "fondo": 23.6,
    "ang": 173.3,
    "rot": 173.3,
    "esc": 2.2
  },
  {
    "id": "t652331",
    "nombre": "Tiendas 3B",
    "dir": "Heroes del 47 SN",
    "cp": "04120",
    "coords": [
      -99.14948,
      19.351351
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 1,
    "en_calle": false,
    "huella": "ok",
    "ancho": 15.7,
    "fondo": 8.3,
    "ang": 176.4,
    "rot": 356.4,
    "esc": 1.34
  },
  {
    "id": "t652335",
    "nombre": "Tiendas 3B",
    "dir": "Calz. de Tlalpan 1770",
    "cp": "04220",
    "coords": [
      -99.144654,
      19.353274
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 20,
    "en_calle": false,
    "huella": "ok",
    "ancho": 17.4,
    "fondo": 12.0,
    "ang": 165.7,
    "rot": 165.7,
    "esc": 1.94
  },
  {
    "id": "t646696",
    "nombre": "Tiendas 3B",
    "dir": "Av Miguel Angel de Quevedo 789",
    "cp": "04330",
    "coords": [
      -99.159614,
      19.343887
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 15,
    "en_calle": false,
    "huella": "ok",
    "ancho": 11.2,
    "fondo": 7.8,
    "ang": 166.9,
    "rot": 166.9,
    "esc": 1.26
  },
  {
    "id": "t646713",
    "nombre": "Tiendas 3B",
    "dir": "Aldama No.29",
    "cp": "06010",
    "coords": [
      -99.135893,
      19.440616
    ],
    "revisar": false,
    "verif": "en edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "ok",
    "ancho": 26.7,
    "fondo": 13.7,
    "ang": 89.6,
    "rot": 89.6,
    "esc": 2.2
  },
  {
    "id": "t607561",
    "nombre": "Tiendas 3B",
    "dir": "Roldan 71",
    "cp": "06090",
    "coords": [
      -99.127066,
      19.426845
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 4,
    "en_calle": false,
    "huella": "ok",
    "ancho": 25.5,
    "fondo": 21.7,
    "ang": 91.7,
    "rot": 271.7,
    "esc": 2.2
  },
  {
    "id": "t171105",
    "nombre": "Tiendas 3B",
    "dir": "Rio Panuco N 147 esq. Rio Tiber",
    "cp": "06500",
    "coords": [
      -99.170764,
      19.429298
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 178,
    "en_calle": false,
    "huella": "ok",
    "ancho": 27.1,
    "fondo": 12.2,
    "ang": 26.1,
    "rot": 26.1,
    "esc": 1.97
  },
  {
    "id": "t646685",
    "nombre": "Tiendas 3B",
    "dir": "Rio Danubio 51 Piso 2",
    "cp": "06500",
    "coords": [
      -99.168886,
      19.431954
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 15,
    "en_calle": false,
    "huella": "ok",
    "ancho": 29.6,
    "fondo": 8.6,
    "ang": 26.2,
    "rot": 206.2,
    "esc": 1.4
  },
  {
    "id": "t646706",
    "nombre": "Tiendas 3B",
    "dir": "Privada Reforma No. 304",
    "cp": "06700",
    "coords": [
      -99.165762,
      19.427299
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 10,
    "en_calle": true,
    "huella": "ok",
    "ancho": 16.7,
    "fondo": 16.5,
    "ang": 27.0,
    "rot": 27.0,
    "esc": 2.0
  },
  {
    "id": "t646589",
    "nombre": "Tiendas 3B",
    "dir": "Avda. Independencia 12",
    "cp": "06720",
    "coords": [
      -99.142128,
      19.433149
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 1,
    "en_calle": false,
    "huella": "grande",
    "ancho": 30.8,
    "fondo": 26.9,
    "ang": 82.2,
    "rot": 82.2,
    "esc": 2.2
  },
  {
    "id": "t646585",
    "nombre": "Tiendas 3B",
    "dir": "Alvaro Obregon S/N",
    "cp": "07000",
    "coords": [
      -99.11656,
      19.479937
    ],
    "revisar": true,
    "verif": "sin edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "ninguna",
    "ang": 0,
    "rot": 0,
    "esc": 1.0
  },
  {
    "id": "t632295",
    "nombre": "Tiendas 3B",
    "dir": "Av. Martin Carrera 4",
    "cp": "07070",
    "coords": [
      -99.111521,
      19.48745
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 6,
    "en_calle": true,
    "huella": "ok",
    "ancho": 6.8,
    "fondo": 3.9,
    "ang": 13.1,
    "rot": 193.1,
    "esc": 0.63
  },
  {
    "id": "t646697",
    "nombre": "Tiendas 3B",
    "dir": "Martin Carrera 159",
    "cp": "07070",
    "coords": [
      -99.105529,
      19.488862
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 218,
    "en_calle": false,
    "huella": "grande",
    "ancho": 86.2,
    "fondo": 31.1,
    "ang": 104.2,
    "rot": 284.2,
    "esc": 2.2
  },
  {
    "id": "t632101",
    "nombre": "Tiendas 3B",
    "dir": "Vicente Guerrero sn",
    "cp": "07070",
    "coords": [
      -99.10545,
      19.488948
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 8,
    "en_calle": true,
    "huella": "grande",
    "ancho": 86.2,
    "fondo": 31.1,
    "ang": 104.2,
    "rot": 284.2,
    "esc": 2.2
  },
  {
    "id": "t646680",
    "nombre": "Tiendas 3B",
    "dir": "Quetzalcoatl sn Mz 8 Lt 14",
    "cp": "07290",
    "coords": [
      -99.13321,
      19.432608
    ],
    "revisar": true,
    "verif": "sin edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "ninguna",
    "ang": 0,
    "rot": 0,
    "esc": 1.0
  },
  {
    "id": "t652494",
    "nombre": "Tiendas 3B",
    "dir": "Sur 149 2107",
    "cp": "08000",
    "coords": [
      -99.100266,
      19.393648
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 9,
    "en_calle": true,
    "huella": "grande",
    "ancho": 32.6,
    "fondo": 9.0,
    "ang": 86.3,
    "rot": 266.3,
    "esc": 1.46
  },
  {
    "id": "t646670",
    "nombre": "Tiendas 3B",
    "dir": "Lote unico, MZ.1",
    "cp": "08000",
    "coords": [
      -99.094595,
      19.392538
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 16,
    "en_calle": false,
    "huella": "ok",
    "ancho": 7.0,
    "fondo": 4.9,
    "ang": 177.7,
    "rot": 357.7,
    "esc": 0.79
  },
  {
    "id": "t646566",
    "nombre": "Tiendas 3B",
    "dir": "Camino Nacional No. 441",
    "cp": "08100",
    "coords": [
      -99.097686,
      19.394751
    ],
    "revisar": true,
    "verif": "ajustada",
    "movida_m": 6,
    "en_calle": false,
    "huella": "grande",
    "ancho": 136.9,
    "fondo": 71.2,
    "ang": 173.5,
    "rot": 173.5,
    "esc": 2.2
  },
  {
    "id": "t632261",
    "nombre": "Tiendas 3B",
    "dir": "Calle 2 Lt7 Mz 8",
    "cp": "08100",
    "coords": [
      -99.083171,
      19.397799
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 2,
    "en_calle": false,
    "huella": "ok",
    "ancho": 17.6,
    "fondo": 16.0,
    "ang": 148.8,
    "rot": 148.8,
    "esc": 2.11
  },
  {
    "id": "t646655",
    "nombre": "Tiendas 3B",
    "dir": "Av. Avila Camacho s/n",
    "cp": "08240",
    "coords": [
      -99.219439,
      19.378571
    ],
    "revisar": true,
    "verif": "ajustada",
    "movida_m": 6,
    "en_calle": true,
    "huella": "grande",
    "ancho": 30.3,
    "fondo": 18.1,
    "ang": 89.7,
    "rot": 269.7,
    "esc": 2.2
  },
  {
    "id": "t652495",
    "nombre": "Tiendas 3B",
    "dir": "Sur 20 140",
    "cp": "08500",
    "coords": [
      -99.08001,
      19.39315
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 34,
    "en_calle": false,
    "huella": "grande",
    "ancho": 104.6,
    "fondo": 93.8,
    "ang": 169.6,
    "rot": 349.6,
    "esc": 2.2
  },
  {
    "id": "t632025",
    "nombre": "Tiendas 3B",
    "dir": "Sur 109 esq Oriente 100 A",
    "cp": "08710",
    "coords": [
      -99.110453,
      19.395835
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 3,
    "en_calle": false,
    "huella": "ok",
    "ancho": 13.3,
    "fondo": 10.3,
    "ang": 174.4,
    "rot": 354.4,
    "esc": 1.59
  },
  {
    "id": "t632282",
    "nombre": "Tiendas 3B",
    "dir": "Ayuntamiento 53",
    "cp": "09000",
    "coords": [
      -99.091143,
      19.361096
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 249,
    "en_calle": false,
    "huella": "ok",
    "ancho": 10.5,
    "fondo": 5.8,
    "ang": 76.8,
    "rot": 256.8,
    "esc": 0.94
  },
  {
    "id": "t646645",
    "nombre": "Tiendas 3B",
    "dir": "Av. Insurgentes Sur No. 179",
    "cp": "09080",
    "coords": [
      -99.163595,
      19.421855
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 6,
    "en_calle": false,
    "huella": "grande",
    "ancho": 34.6,
    "fondo": 28.7,
    "ang": 74.9,
    "rot": 74.9,
    "esc": 2.2
  },
  {
    "id": "t646635",
    "nombre": "Tiendas 3B",
    "dir": "16 de septiembre, Lt.5, Mz.1",
    "cp": "09326",
    "coords": [
      -99.058482,
      19.315325
    ],
    "revisar": true,
    "verif": "en edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "ok",
    "ancho": 10.5,
    "fondo": 8.2,
    "ang": 145.6,
    "rot": 145.6,
    "esc": 1.25
  },
  {
    "id": "t632089",
    "nombre": "Tiendas 3B",
    "dir": "Mina SN",
    "cp": "09360",
    "coords": [
      -99.08227,
      19.356129
    ],
    "revisar": false,
    "verif": "en edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "grande",
    "ancho": 31.5,
    "fondo": 20.2,
    "ang": 79.7,
    "rot": 79.7,
    "esc": 2.2
  },
  {
    "id": "t632204",
    "nombre": "Tiendas 3B",
    "dir": "Cuauhtemoc No 30",
    "cp": "09790",
    "coords": [
      -99.08993,
      19.36156
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 0,
    "en_calle": false,
    "huella": "ok",
    "ancho": 18.6,
    "fondo": 13.9,
    "ang": 70.0,
    "rot": 250.0,
    "esc": 2.2
  },
  {
    "id": "t646627",
    "nombre": "Tiendas 3B",
    "dir": "Calz. Ermita Iztapalapa N 701 esq. Trojes",
    "cp": "09810",
    "coords": [
      -99.109187,
      19.356124
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 13,
    "en_calle": true,
    "huella": "ok",
    "ancho": 13.5,
    "fondo": 4.5,
    "ang": 178.2,
    "rot": 358.2,
    "esc": 0.72
  },
  {
    "id": "t646643",
    "nombre": "Tiendas 3B",
    "dir": "Calle 16 de Septiembre Numero 23",
    "cp": "09810",
    "coords": [
      -99.207842,
      19.392382
    ],
    "revisar": true,
    "verif": "ajustada",
    "movida_m": 9,
    "en_calle": true,
    "huella": "ok",
    "ancho": 18.9,
    "fondo": 16.8,
    "ang": 13.7,
    "rot": 193.7,
    "esc": 2.2
  },
  {
    "id": "t652509",
    "nombre": "Tiendas 3B",
    "dir": "Chimacoatl 13",
    "cp": "09820",
    "coords": [
      -99.099062,
      19.351635
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 200,
    "en_calle": false,
    "huella": "grande",
    "ancho": 97.9,
    "fondo": 56.7,
    "ang": 71.2,
    "rot": 251.2,
    "esc": 2.2
  },
  {
    "id": "t646535",
    "nombre": "Tiendas 3B",
    "dir": "Hidalgo y Bravo S/N",
    "cp": "09930",
    "coords": [
      -99.0661,
      19.301998
    ],
    "revisar": false,
    "verif": "en edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "ok",
    "ancho": 7.1,
    "fondo": 3.1,
    "ang": 88.8,
    "rot": 88.8,
    "esc": 0.5
  },
  {
    "id": "t646620",
    "nombre": "Tiendas 3B",
    "dir": "Crucero Carmona S/N",
    "cp": "11300",
    "coords": [
      -99.17399,
      19.436516
    ],
    "revisar": false,
    "verif": "en edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "grande",
    "ancho": 78.2,
    "fondo": 45.0,
    "ang": 151.3,
    "rot": 151.3,
    "esc": 2.2
  },
  {
    "id": "t646528",
    "nombre": "Tiendas 3B",
    "dir": "21 Mz 17 Lt10",
    "cp": "13010",
    "coords": [
      -99.043924,
      19.299058
    ],
    "revisar": true,
    "verif": "ajustada",
    "movida_m": 24,
    "en_calle": false,
    "huella": "ok",
    "ancho": 15.1,
    "fondo": 9.2,
    "ang": 91.1,
    "rot": 91.1,
    "esc": 1.48
  },
  {
    "id": "t652878",
    "nombre": "Tiendas 3B",
    "dir": "Ricardo Monges López 7",
    "cp": "13220",
    "coords": [
      -99.05512,
      19.300317
    ],
    "revisar": false,
    "verif": "en edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "grande",
    "ancho": 33.2,
    "fondo": 18.4,
    "ang": 52.4,
    "rot": 52.4,
    "esc": 2.2
  },
  {
    "id": "t632182",
    "nombre": "Tiendas 3B",
    "dir": "Gallo de Oro 189",
    "cp": "13220",
    "coords": [
      -99.055007,
      19.295098
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 5,
    "en_calle": true,
    "huella": "ok",
    "ancho": 18.5,
    "fondo": 12.4,
    "ang": 55.0,
    "rot": 235.0,
    "esc": 2.01
  },
  {
    "id": "t632038",
    "nombre": "Tiendas 3B",
    "dir": "Calle Diaz Miron sn",
    "cp": "13319",
    "coords": [
      -99.043925,
      19.306002
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 2,
    "en_calle": true,
    "huella": "ok",
    "ancho": 10.8,
    "fondo": 6.1,
    "ang": 58.6,
    "rot": 58.6,
    "esc": 0.99
  },
  {
    "id": "t646582",
    "nombre": "Tiendas 3B",
    "dir": "Dzemul Mz. 153 Lt 2",
    "cp": "14100",
    "coords": [
      -99.211402,
      19.279148
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 7,
    "en_calle": true,
    "huella": "grande",
    "ancho": 40.7,
    "fondo": 4.7,
    "ang": 157.9,
    "rot": 337.9,
    "esc": 0.75
  },
  {
    "id": "t632335",
    "nombre": "Tiendas 3B",
    "dir": "Av Chicoasen 160 Mz 54 L 1",
    "cp": "14240",
    "coords": [
      -99.229668,
      19.289778
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 3,
    "en_calle": true,
    "huella": "ok",
    "ancho": 13.0,
    "fondo": 6.3,
    "ang": 4.9,
    "rot": 184.9,
    "esc": 1.02
  },
  {
    "id": "t632366",
    "nombre": "Tiendas 3B",
    "dir": "Alfredo V. Bonfil Lt2 Mz160 Zona2",
    "cp": "14250",
    "coords": [
      -99.202072,
      19.278802
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 3,
    "en_calle": true,
    "huella": "ok",
    "ancho": 11.2,
    "fondo": 8.2,
    "ang": 109.9,
    "rot": 109.9,
    "esc": 1.33
  },
  {
    "id": "t632020",
    "nombre": "Tiendas 3B",
    "dir": "Valentin Gama y Cruz, sn",
    "cp": "14260",
    "coords": [
      -99.188473,
      19.284723
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 7,
    "en_calle": true,
    "huella": "ok",
    "ancho": 20.4,
    "fondo": 5.9,
    "ang": 65.4,
    "rot": 245.4,
    "esc": 0.95
  },
  {
    "id": "t632296",
    "nombre": "Tiendas 3B",
    "dir": "Av Mexico Ajusco Nr 40",
    "cp": "14480",
    "coords": [
      -99.16722,
      19.234308
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 13,
    "en_calle": false,
    "huella": "ok",
    "ancho": 6.1,
    "fondo": 3.4,
    "ang": 177.4,
    "rot": 177.4,
    "esc": 0.54
  },
  {
    "id": "t646581",
    "nombre": "Tiendas 3B",
    "dir": "Camino a San Pedro Martir, Mz81 Lt.12",
    "cp": "14640",
    "coords": [
      -99.159537,
      19.271729
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 9,
    "en_calle": false,
    "huella": "ok",
    "ancho": 24.1,
    "fondo": 11.3,
    "ang": 72.7,
    "rot": 252.7,
    "esc": 1.83
  },
  {
    "id": "t632133",
    "nombre": "Tiendas 3B",
    "dir": "Miguel Hidalgo 77",
    "cp": "14710",
    "coords": [
      -99.160753,
      19.28602
    ],
    "revisar": true,
    "verif": "ajustada",
    "movida_m": 4,
    "en_calle": true,
    "huella": "ok",
    "ancho": 12.8,
    "fondo": 10.1,
    "ang": 162.2,
    "rot": 342.2,
    "esc": 1.53
  },
  {
    "id": "t632085",
    "nombre": "Tiendas 3B",
    "dir": "Morelos 7",
    "cp": "14710",
    "coords": [
      -99.188739,
      19.284026
    ],
    "revisar": true,
    "verif": "ajustada",
    "movida_m": 2,
    "en_calle": true,
    "huella": "ok",
    "ancho": 11.0,
    "fondo": 8.7,
    "ang": 33.7,
    "rot": 33.7,
    "esc": 1.32
  },
  {
    "id": "t646518",
    "nombre": "Tiendas 3B",
    "dir": "Jose Maria Morelos 15",
    "cp": "14710",
    "coords": [
      -99.209269,
      19.214598
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 1,
    "en_calle": true,
    "huella": "ok",
    "ancho": 7.8,
    "fondo": 4.9,
    "ang": 110.2,
    "rot": 290.2,
    "esc": 0.8
  },
  {
    "id": "t632352",
    "nombre": "Tiendas 3B",
    "dir": "Av. 10 N 142",
    "cp": "15000",
    "coords": [
      -99.092118,
      19.412553
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 13,
    "en_calle": false,
    "huella": "ok",
    "ancho": 25.6,
    "fondo": 9.9,
    "ang": 61.6,
    "rot": 241.6,
    "esc": 1.6
  },
  {
    "id": "t646565",
    "nombre": "Tiendas 3B",
    "dir": "Jose Rivera N 45",
    "cp": "15500",
    "coords": [
      -99.107525,
      19.427761
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 8,
    "en_calle": true,
    "huella": "ok",
    "ancho": 13.3,
    "fondo": 10.3,
    "ang": 152.2,
    "rot": 332.2,
    "esc": 1.6
  },
  {
    "id": "t653561",
    "nombre": "Tiendas 3B",
    "dir": "Eje 1 Nte.",
    "cp": "15530",
    "coords": [
      -99.107617,
      19.433557
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 26,
    "en_calle": true,
    "huella": "ok",
    "ancho": 24.4,
    "fondo": 8.9,
    "ang": 62.8,
    "rot": 62.8,
    "esc": 1.43
  },
  {
    "id": "t646575",
    "nombre": "Tiendas 3B",
    "dir": "Juan A. Mateos No.445",
    "cp": "15840",
    "coords": [
      -99.124581,
      19.40997
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 8,
    "en_calle": false,
    "huella": "ok",
    "ancho": 20.7,
    "fondo": 15.5,
    "ang": 1.5,
    "rot": 181.5,
    "esc": 2.2
  },
  {
    "id": "t632132",
    "nombre": "Tiendas 3B",
    "dir": "Camelinas No. 127",
    "cp": "15850",
    "coords": [
      -99.119455,
      19.410969
    ],
    "revisar": false,
    "verif": "en edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "ok",
    "ancho": 17.8,
    "fondo": 11.7,
    "ang": 173.2,
    "rot": 173.2,
    "esc": 1.89
  },
  {
    "id": "t646514",
    "nombre": "Tiendas 3B",
    "dir": "Jose Maria Roa Barcenas 391",
    "cp": "15850",
    "coords": [
      -99.13162,
      19.410839
    ],
    "revisar": false,
    "verif": "en edificio",
    "movida_m": 0,
    "en_calle": false,
    "huella": "ok",
    "ancho": 15.1,
    "fondo": 7.9,
    "ang": 173.1,
    "rot": 173.1,
    "esc": 1.28
  },
  {
    "id": "t646570",
    "nombre": "Tiendas 3B",
    "dir": "Av. 20 de Noviembre #738",
    "cp": "16020",
    "coords": [
      -99.128937,
      19.27059
    ],
    "revisar": false,
    "verif": "ajustada",
    "movida_m": 6,
    "en_calle": true,
    "huella": "ok",
    "ancho": 10.1,
    "fondo": 8.8,
    "ang": 171.6,
    "rot": 351.6,
    "esc": 1.21
  },
  {
    "id": "t646513",
    "nombre": "Tiendas 3B",
    "dir": "Rubellon 46",
    "cp": "16030",
    "coords": [
      -99.119209,
      19.269534
    ],
    "revisar": false,
    "verif": "verificada",
    "movida_m": 25,
    "en_calle": false,
    "huella": "ok",
    "ancho": 25.7,
    "fondo": 7.5,
    "ang": 167.4,
    "rot": 347.4,
    "esc": 1.21
  }
];
