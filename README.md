# 2024-1 / IIC2173 - E0 | CoolGoat Async

# Dominio
- [numby.me](https://numby.me)
- [www.numby.me](https://www.numby.me)

_"...the Warp Trotter "[Numby](https://honkai-star-rail.fandom.com/wiki/Topaz_and_Numby)," is also capable of acutely perceiving where "riches" are located. It can even perform jobs involving security, debt collection, and actuarial sciences."_

# Consideraciones generales

- El root directory ```/``` redirige automáticamente a ```/fixtures```.
- Se definio el atributo ```flag``` de ```league``` como ```<string|null>``` para ajustrse a los nuevos partidos del ```02/09/2024```.
- El endpoint ```/fixtures{:identifier}``` utiliza el ```id``` del _nested object_ ```fixtures``` para identificar los partidos.
- El parámetro ```page``` en el endpoint ```/fixtures``` comienza desde ```0```.
