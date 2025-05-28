const require = createRequire(import.meta.url);
import bcfetch from 'bandcamp-fetch';
import { createRequire } from "module";
const readline = require('readline');


const fetchBandcampData = async(cookie) => {
    bcfetch.setCookie(cookie.toString())
    const fan = bcfetch.fan
    const wishlist = await fan.getWishlist()

    const validKeys = ["name", "artist", "featuredTrack"]
    const filteredElements = []
    wishlist.items.forEach((element) => {
        const filteredArr = Object.entries(element).filter(([key, _]) => validKeys.includes(key))
        const filteredObj = Object.fromEntries(filteredArr)

        filteredObj.artist = filteredObj.artist.name
        filteredObj["album"] = filteredObj.name
        filteredObj["title"] = filteredObj.featuredTrack.name
        delete filteredObj["name"]
        delete filteredObj["featuredTrack"]
        filteredElements.push(filteredObj)
    })
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
