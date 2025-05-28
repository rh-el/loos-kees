// const require = createRequire(import.meta.url);
import bcfetch from 'bandcamp-fetch';
// import { createRequire } from "module";
// const readline = require('readline');

const getAlbumTracklist = async (albumUrl) => {
    const params = {albumUrl: albumUrl}
    const album = bcfetch.album
    const info = await album.getInfo(params)
    const filteredTracks = []
    info.tracks.forEach((track) => {
        filteredTracks.push(track.name)
    })
    return filteredTracks
}

const fetchBandcampData = async (cookie) => {
    bcfetch.setCookie(cookie.toString())
    const fan = bcfetch.fan
    const wishlist = await fan.getWishlist()
    const validKeys = ["name", "artist", "featuredTrack"]

    const promises = wishlist.items.map(async (element) => {
        const albumUrl = element["url"]
        const tracklist = await getAlbumTracklist(albumUrl)

        const filteredArr = Object.entries(element).filter(([key, _]) => validKeys.includes(key))
        const filteredObj = Object.fromEntries(filteredArr)

        filteredObj.artist = filteredObj.artist.name
        filteredObj.album = filteredObj.name
        filteredObj.tracks = tracklist

        delete filteredObj.name
        delete filteredObj.featuredTrack

        return filteredObj
    })
    const filteredElements = await Promise.all(promises)
    console.log(JSON.stringify(filteredElements))
}

if (process.argv.length > 2) {
    const cookie = process.argv[2];
    fetchBandcampData(cookie)
} else {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    rl.question("enter your bandcamp cookie: ", async (cookie) => {
        await fetchBandcampData(cookie)
        rl.close()
    })
}
