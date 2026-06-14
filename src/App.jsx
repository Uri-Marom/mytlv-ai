import { useState, useMemo, useEffect } from "react";

// ── Live database (27 real events + 351 similarity pairs) ──────────────────
const DB = {"events":[{"id":1,"source":"secret_tel_aviv","title":"Pride in Tel Aviv 2026 Guide","description":"Pride Month in Tel Aviv is back 🏳️‍🌈","category":"cultural","subcategory":"pride","sta_category":"parties","venue_name":"All over Tel Aviv","neighborhood":"City Center","event_date":"2026-06-14","start_time":"12:00","end_time":"23:50","price_min":0,"price_max":null,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/274c583ae12c13dd75af1e46e22d4859.jpeg","ticket_url":null,"source_url":"https://www.secrettelaviv.com/tickets/pride-month-in-tel-aviv-2026-around-tel-aviv","tags":["Pride","Free","All Weekend"]},{"id":2,"source":"secret_tel_aviv","title":"St. Tropez Part 2 by Olim in TLV @ Loullie","description":"Beach vibes in the heart of TLV 🪩","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"Loullie","neighborhood":"Tel Aviv Port","event_date":"2026-06-16","start_time":"17:00","end_time":"23:55","price_min":80,"price_max":120,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-101.jpg","ticket_url":"https://www.entrio.co.il/event/st-tropez","source_url":"https://www.secrettelaviv.com/tickets/st-tropez-part-2-by-olim-in-tlv-loullie","tags":["Electronic","Beach Vibes","Expats"]},{"id":3,"source":"secret_tel_aviv","title":"Off Grid 360 Edition @ Kuli Alma","description":"Epic grooves and good vibes at Kuli Alma 💅🏻","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"Kuli Alma","neighborhood":"Florentin","event_date":"2026-06-17","start_time":"21:00","end_time":"23:50","price_min":60,"price_max":90,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-243.jpg","ticket_url":"https://www.entrio.co.il/event/off-grid","source_url":"https://www.secrettelaviv.com/tickets/off-grid-360-edition-kuli-alma-4","tags":["Techno","Underground","Kuli Alma"]},{"id":4,"source":"secret_tel_aviv","title":"Live From the Storm by Shalev Saar × Editions Pop Up @ Soho House Tel Aviv","description":"Art exhibition with live music and surprises 🖼️","category":"cultural","subcategory":"exhibition","sta_category":"parties","venue_name":"Soho House Tel Aviv","neighborhood":"Rothschild","event_date":"2026-06-18","start_time":"18:30","end_time":"23:00","price_min":0,"price_max":null,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-151.jpg","ticket_url":null,"source_url":"https://www.secrettelaviv.com/tickets/live-from-the-storm-by-shalev-saar-x-editions-pop-up-soho-house-tel-aviv","tags":["Art","Live Music","Pop Up","Soho House"]},{"id":5,"source":"secret_tel_aviv","title":"Reading Party × Beit Ariela @ Beit Radical","description":"Literary reading party at Beit Radical ✨","category":"cultural","subcategory":"meetup","sta_category":"parties","venue_name":"Beit Radical","neighborhood":"City Center","event_date":"2026-06-18","start_time":"19:00","end_time":"22:00","price_min":0,"price_max":null,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-126.jpg","ticket_url":null,"source_url":"https://www.secrettelaviv.com/tickets/reading-party-x-beit-ariela-beit-radical","tags":["Literature","Culture","Free"]},{"id":6,"source":"secret_tel_aviv","title":"Slice of Gathering @ HaEzor","description":"Grateful Dead-themed night of music and fun 🤩","category":"music","subcategory":"live","sta_category":"parties","venue_name":"HaEzor","neighborhood":"South TLV","event_date":"2026-06-18","start_time":"20:00","end_time":"23:00","price_min":50,"price_max":70,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-199.jpg","ticket_url":"https://www.entrio.co.il/event/slice-gathering","source_url":"https://www.secrettelaviv.com/tickets/slice-of-gathering-haezor","tags":["Grateful Dead","Rock","Live Band"]},{"id":7,"source":"secret_tel_aviv","title":"Down The Rabbit Hole @ Shalvata","description":"Psychedelic summer kickoff at Shalvata 🐰","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"Shalvata","neighborhood":"Tel Aviv Port","event_date":"2026-06-18","start_time":"22:30","end_time":"23:55","price_min":90,"price_max":130,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-201.jpg","ticket_url":"https://www.entrio.co.il/event/rabbit-hole","source_url":"https://www.secrettelaviv.com/tickets/down-the-rabbit-hole-shalvata","tags":["Psychedelic","Electronic","Late Night"]},{"id":8,"source":"secret_tel_aviv","title":"Fuego.TLV — Noche Latina @ HaTnufa 7","description":"Get ready for an unforgettable Latin party 💃🏻","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"HaTnufa 7","neighborhood":"City Center","event_date":"2026-06-18","start_time":"23:00","end_time":"23:55","price_min":80,"price_max":100,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-162.jpg","ticket_url":"https://www.entrio.co.il/event/fuego","source_url":"https://www.secrettelaviv.com/tickets/fuego-tlv-noche-latina-hatnufa-7","tags":["Latin","Salsa","Party"]},{"id":9,"source":"secret_tel_aviv","title":"RHINO — A Queer Party @ Levontin 7","description":"Queer runway party at Levontin 7 🏳️‍🌈","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"Levontin 7","neighborhood":"Florentin","event_date":"2026-06-18","start_time":"23:00","end_time":"23:55","price_min":60,"price_max":80,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-202.jpg","ticket_url":"https://www.entrio.co.il/event/rhino","source_url":"https://www.secrettelaviv.com/tickets/rhino-a-queer-party-levontin-7","tags":["Pride","Queer","Electronic"]},{"id":10,"source":"secret_tel_aviv","title":"Swifties Rave — The Eras Edition @ Duplex","description":"Join the Swifties for a powerful rave 💅🏻","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"Duplex","neighborhood":"City Center","event_date":"2026-06-18","start_time":"23:00","end_time":"23:55","price_min":70,"price_max":100,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-203.jpg","ticket_url":"https://www.entrio.co.il/event/swifties","source_url":"https://www.secrettelaviv.com/tickets/swifties-rave-the-eras-edition-duplex","tags":["Pop","Taylor Swift","Party"]},{"id":11,"source":"secret_tel_aviv","title":"Captain Hook, Crocoloko & More @ Haoman 17","description":"Epic tech and trance night at Haoman 17 💃🏻","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"Haoman 17","neighborhood":"South TLV","event_date":"2026-06-18","start_time":"23:00","end_time":"23:55","price_min":100,"price_max":150,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-204.jpg","ticket_url":"https://www.entrio.co.il/event/haoman","source_url":"https://www.secrettelaviv.com/tickets/thursday-night-with-captain-hook-crocoloko-and-more-haoman-17","tags":["Psytrance","Trance","Haoman 17","Big Club"]},{"id":20,"source":"entrio","title":"Nachalat Binyamin Crafts Fair","description":"The iconic outdoor crafts fair — artists, jewellery, ceramics every Friday & Saturday.","category":"market","subcategory":"crafts","sta_category":"shopping","venue_name":"Nachalat Binyamin Street","neighborhood":"City Center","event_date":"2026-06-19","start_time":"10:00","end_time":"18:00","price_min":0,"price_max":null,"image_url":null,"ticket_url":null,"source_url":"https://www.entrio.co.il/event/nachalat","tags":["Crafts","Market","Outdoor","Free","Family"]},{"id":27,"source":"tel_aviv_municipality","title":"Shuk HaNamal Night Market","description":"Tel Aviv Port's Friday night food & artisan market.","category":"market","subcategory":"food","sta_category":"food-events","venue_name":"Tel Aviv Port","neighborhood":"North TLV","event_date":"2026-06-19","start_time":"18:00","end_time":"23:00","price_min":0,"price_max":null,"image_url":null,"ticket_url":null,"source_url":"https://www.namal.co.il","tags":["Food","Market","Night Market","Port","Free"]},{"id":26,"source":"tel_aviv_municipality","title":"Cinematheque — Amos Gitai Retrospective","description":"A retrospective of Israel's most important auteur filmmaker.","category":"cultural","subcategory":"film","sta_category":"culture-highlights","venue_name":"Tel Aviv Cinematheque","neighborhood":"City Center","event_date":"2026-06-19","start_time":"19:00","end_time":"21:30","price_min":45,"price_max":55,"image_url":null,"ticket_url":"https://www.cinematheque.co.il","source_url":"https://www.cinematheque.co.il","tags":["Cinema","Israeli Film","Retrospective"]},{"id":18,"source":"entrio","title":"Barby Friday Night — Local Bands Showcase","description":"Barby Club's weekly showcase of the best local Israeli acts.","category":"music","subcategory":"live","sta_category":"live-music","venue_name":"Barby Club","neighborhood":"Florentin","event_date":"2026-06-19","start_time":"21:00","end_time":"23:55","price_min":80,"price_max":100,"image_url":null,"ticket_url":"https://www.entrio.co.il/event/barby-fri","source_url":"https://www.entrio.co.il/event/barby-fri","tags":["Israeli Rock","Live Band","Barby"]},{"id":24,"source":"bandsintown","title":"Dudu Tassa & The Kuwaitis","description":"Middle Eastern sounds — Dudu Tassa's iconic show at Reading 3.","category":"music","subcategory":"live","sta_category":"live-music","venue_name":"Reading 3","neighborhood":"North TLV","event_date":"2026-06-19","start_time":"21:00","end_time":"23:00","price_min":130,"price_max":180,"image_url":null,"ticket_url":"https://www.ticketmaster.co.il","source_url":"https://www.bandsintown.com/e/dudu-tassa","tags":["World Music","Arabic","Israeli","Live Band"]},{"id":22,"source":"entrio","title":"Jaffa Flea Market","description":"HaPishpeshim — Tel Aviv's best flea market. Vintage, antiques, street food.","category":"market","subcategory":"flea","sta_category":"shopping","venue_name":"HaPishpeshim Market, Jaffa","neighborhood":"Jaffa","event_date":"2026-06-20","start_time":"08:00","end_time":"16:00","price_min":0,"price_max":null,"image_url":null,"ticket_url":null,"source_url":"https://www.entrio.co.il/event/jaffa-flea","tags":["Vintage","Antiques","Jaffa","Free","Market"]},{"id":25,"source":"tel_aviv_municipality","title":"Bauhaus Heritage Walking Tour","description":"UNESCO World Heritage Site tour of Tel Aviv's White City architecture.","category":"cultural","subcategory":"tour","sta_category":"culture-highlights","venue_name":"Rothschild Boulevard","neighborhood":"City Center","event_date":"2026-06-20","start_time":"09:00","end_time":"11:00","price_min":35,"price_max":35,"image_url":null,"ticket_url":null,"source_url":"https://www.tel-aviv.gov.il","tags":["Architecture","History","UNESCO","Tour"]},{"id":21,"source":"entrio","title":"Nachalat Binyamin Crafts Fair","description":"The iconic outdoor crafts fair — artists, jewellery, ceramics every Friday & Saturday.","category":"market","subcategory":"crafts","sta_category":"shopping","venue_name":"Nachalat Binyamin Street","neighborhood":"City Center","event_date":"2026-06-20","start_time":"10:00","end_time":"18:00","price_min":0,"price_max":null,"image_url":null,"ticket_url":null,"source_url":"https://www.entrio.co.il/event/nachalat-sat","tags":["Crafts","Market","Outdoor","Free","Family"]},{"id":12,"source":"secret_tel_aviv","title":"Saturday Day Party: DARCO × Castanieta Live @ Shalvata","description":"Epic Saturday party with DARCO and Castanieta ✨","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"Shalvata","neighborhood":"Tel Aviv Port","event_date":"2026-06-20","start_time":"15:00","end_time":"22:00","price_min":80,"price_max":120,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-6.jpg","ticket_url":"https://www.entrio.co.il/event/darco","source_url":"https://www.secrettelaviv.com/tickets/saturday-day-party-darco-x-castanieta-live-shalvata","tags":["Day Party","Electronic","Live Band","Port"]},{"id":13,"source":"secret_tel_aviv","title":"Summer Time Wine Festival & Sunset Party @ Moonchild","description":"Sip unlimited wine at sunset festival 🍷","category":"market","subcategory":"food","sta_category":"food-events","venue_name":"Moonchild","neighborhood":"Florentin","event_date":"2026-06-20","start_time":"17:00","end_time":"22:30","price_min":120,"price_max":180,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-208.jpg","ticket_url":"https://www.entrio.co.il/event/wine-festival","source_url":"https://www.secrettelaviv.com/tickets/cheers-x-myyain-summer-time-wine-festival-sunset-party-moonchild","tags":["Wine","Sunset","Festival","Food"]},{"id":23,"source":"bandsintown","title":"Infected Mushroom","description":"Psytrance legends Infected Mushroom — outdoor summer show.","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"Park Ariel Sharon","neighborhood":"South TLV","event_date":"2026-06-20","start_time":"22:00","end_time":"23:55","price_min":140,"price_max":200,"image_url":null,"ticket_url":"https://www.ticketmaster.co.il","source_url":"https://www.bandsintown.com/e/infected-mushroom-tlv","tags":["Psytrance","Electronic","Outdoor","Israeli"]},{"id":19,"source":"entrio","title":"The Block Saturday Techno Night","description":"Berlin-style industrial techno at The Block.","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"The Block","neighborhood":"Florentin","event_date":"2026-06-20","start_time":"23:00","end_time":"23:55","price_min":100,"price_max":150,"image_url":null,"ticket_url":"https://www.entrio.co.il/event/block-sat","source_url":"https://www.entrio.co.il/event/block-sat","tags":["Techno","Industrial","Club"]},{"id":14,"source":"secret_tel_aviv","title":"Memories Opening Summer @ Gagarin Club","description":"Massive summer fest at Gagarin Club 🪩","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"Gagarin Club","neighborhood":"South TLV","event_date":"2026-06-21","start_time":"22:00","end_time":"23:50","price_min":100,"price_max":150,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-84.jpg","ticket_url":"https://www.entrio.co.il/event/memories","source_url":"https://www.secrettelaviv.com/tickets/memories-opening-summer-gagarin-club","tags":["Electronic","Club","Summer Opening"]},{"id":17,"source":"secret_tel_aviv","title":"Nostalgic Israeli Music Quiz + Party @ Mike's Place","description":"Nostalgic Israeli music quiz and party 🧠","category":"music","subcategory":"live","sta_category":"live-music","venue_name":"Mike's Place Tel Aviv","neighborhood":"City Center","event_date":"2026-06-24","start_time":"20:45","end_time":"22:30","price_min":0,"price_max":null,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/06/image-220.jpg","ticket_url":null,"source_url":"https://www.secrettelaviv.com/tickets/nostalgic-israeli-music-quiz-party-mikes-place","tags":["Israeli Music","Quiz","Pub","English Friendly"]},{"id":16,"source":"secret_tel_aviv","title":"Laila Lavan — White Night Tel Aviv 2026","description":"Tel Aviv's White Night celebration — all night parties across the city!","category":"cultural","subcategory":"festival","sta_category":"holidays","venue_name":"All over Tel Aviv","neighborhood":"City Center","event_date":"2026-06-25","start_time":"20:00","end_time":"23:55","price_min":0,"price_max":null,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2017/05/laila-lavan-button.png","ticket_url":null,"source_url":"https://www.secrettelaviv.com/tickets/laila-lavan-white-night-tel-aviv","tags":["White Night","Free","City Festival","All Venues"]},{"id":15,"source":"secret_tel_aviv","title":"Magit Cacoon @ Minus One","description":"Catch Magit Cacoon live at Minus One 💃🏻","category":"music","subcategory":"dj-set","sta_category":"parties","venue_name":"Minus One","neighborhood":"South TLV","event_date":"2026-06-25","start_time":"23:30","end_time":"23:55","price_min":120,"price_max":180,"image_url":"https://www.secrettelaviv.com/wp-content/uploads/2026/05/image-52.jpg","ticket_url":"https://www.entrio.co.il/event/magit","source_url":"https://www.secrettelaviv.com/tickets/magit-cacoon-minus-one","tags":["Techno","International DJ","White Night"]}],"similarity":[{"event_a_id":2,"event_b_id":12,"score_user_overlap":0.6723,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.6874,"overlap_user_count":558},{"event_a_id":7,"event_b_id":12,"score_user_overlap":0.7056,"score_venue":1.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.6874,"overlap_user_count":556},{"event_a_id":11,"event_b_id":15,"score_user_overlap":0.6285,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.6611,"overlap_user_count":587},{"event_a_id":15,"event_b_id":23,"score_user_overlap":0.5873,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.6364,"overlap_user_count":585},{"event_a_id":9,"event_b_id":19,"score_user_overlap":0.5854,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.6353,"overlap_user_count":579},{"event_a_id":14,"event_b_id":15,"score_user_overlap":0.5804,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.6322,"overlap_user_count":574},{"event_a_id":8,"event_b_id":10,"score_user_overlap":0.577,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.6302,"overlap_user_count":611},{"event_a_id":3,"event_b_id":19,"score_user_overlap":0.5669,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.6241,"overlap_user_count":585},{"event_a_id":3,"event_b_id":9,"score_user_overlap":0.5634,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.622,"overlap_user_count":582},{"event_a_id":11,"event_b_id":23,"score_user_overlap":0.5553,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.6172,"overlap_user_count":592},{"event_a_id":11,"event_b_id":14,"score_user_overlap":0.5545,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.6167,"overlap_user_count":585},{"event_a_id":14,"event_b_id":23,"score_user_overlap":0.5357,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.6054,"overlap_user_count":593},{"event_a_id":7,"event_b_id":15,"score_user_overlap":0.6675,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5845,"overlap_user_count":554},{"event_a_id":2,"event_b_id":7,"score_user_overlap":0.6952,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.5811,"overlap_user_count":561},{"event_a_id":7,"event_b_id":9,"score_user_overlap":0.6346,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5648,"overlap_user_count":561},{"event_a_id":7,"event_b_id":11,"score_user_overlap":0.6251,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5591,"overlap_user_count":562},{"event_a_id":7,"event_b_id":19,"score_user_overlap":0.624,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5584,"overlap_user_count":556},{"event_a_id":3,"event_b_id":7,"score_user_overlap":0.6047,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5468,"overlap_user_count":563},{"event_a_id":7,"event_b_id":10,"score_user_overlap":0.6,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.544,"overlap_user_count":564},{"event_a_id":15,"event_b_id":19,"score_user_overlap":0.5947,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5408,"overlap_user_count":562},{"event_a_id":7,"event_b_id":14,"score_user_overlap":0.5938,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5403,"overlap_user_count":560},{"event_a_id":7,"event_b_id":8,"score_user_overlap":0.5936,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5401,"overlap_user_count":555},{"event_a_id":9,"event_b_id":15,"score_user_overlap":0.5926,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5396,"overlap_user_count":560},{"event_a_id":7,"event_b_id":23,"score_user_overlap":0.5844,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5346,"overlap_user_count":561},{"event_a_id":3,"event_b_id":15,"score_user_overlap":0.5793,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5316,"overlap_user_count":570},{"event_a_id":10,"event_b_id":15,"score_user_overlap":0.5719,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5271,"overlap_user_count":569},{"event_a_id":8,"event_b_id":15,"score_user_overlap":0.5657,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5234,"overlap_user_count":560},{"event_a_id":20,"event_b_id":21,"score_user_overlap":0.226,"score_venue":1.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5196,"overlap_user_count":146},{"event_a_id":9,"event_b_id":11,"score_user_overlap":0.5586,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5192,"overlap_user_count":567},{"event_a_id":10,"event_b_id":19,"score_user_overlap":0.5569,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5182,"overlap_user_count":582},{"event_a_id":3,"event_b_id":11,"score_user_overlap":0.5548,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5169,"overlap_user_count":582},{"event_a_id":8,"event_b_id":9,"score_user_overlap":0.5535,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5161,"overlap_user_count":574},{"event_a_id":11,"event_b_id":19,"score_user_overlap":0.5529,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5158,"overlap_user_count":564},{"event_a_id":9,"event_b_id":10,"score_user_overlap":0.5476,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5126,"overlap_user_count":575},{"event_a_id":8,"event_b_id":11,"score_user_overlap":0.5466,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5119,"overlap_user_count":575},{"event_a_id":3,"event_b_id":10,"score_user_overlap":0.5457,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5114,"overlap_user_count":591},{"event_a_id":9,"event_b_id":14,"score_user_overlap":0.5452,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5111,"overlap_user_count":573},{"event_a_id":10,"event_b_id":11,"score_user_overlap":0.5452,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5111,"overlap_user_count":579},{"event_a_id":8,"event_b_id":19,"score_user_overlap":0.545,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.511,"overlap_user_count":569},{"event_a_id":19,"event_b_id":23,"score_user_overlap":0.5408,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5085,"overlap_user_count":577},{"event_a_id":9,"event_b_id":23,"score_user_overlap":0.5403,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5082,"overlap_user_count":576},{"event_a_id":9,"event_b_id":18,"score_user_overlap":0.4262,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.5077,"overlap_user_count":453},{"event_a_id":3,"event_b_id":8,"score_user_overlap":0.5385,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5071,"overlap_user_count":581},{"event_a_id":6,"event_b_id":14,"score_user_overlap":0.4252,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.5071,"overlap_user_count":432},{"event_a_id":14,"event_b_id":19,"score_user_overlap":0.5383,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.507,"overlap_user_count":569},{"event_a_id":8,"event_b_id":14,"score_user_overlap":0.5354,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5053,"overlap_user_count":582},{"event_a_id":3,"event_b_id":18,"score_user_overlap":0.4163,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.5018,"overlap_user_count":460},{"event_a_id":18,"event_b_id":19,"score_user_overlap":0.416,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.5016,"overlap_user_count":446},{"event_a_id":10,"event_b_id":14,"score_user_overlap":0.5286,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5012,"overlap_user_count":582},{"event_a_id":6,"event_b_id":23,"score_user_overlap":0.4151,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.501,"overlap_user_count":430},{"event_a_id":10,"event_b_id":23,"score_user_overlap":0.5269,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.5002,"overlap_user_count":587},{"event_a_id":3,"event_b_id":23,"score_user_overlap":0.5262,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.4997,"overlap_user_count":583},{"event_a_id":3,"event_b_id":14,"score_user_overlap":0.5237,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.4982,"overlap_user_count":575},{"event_a_id":6,"event_b_id":24,"score_user_overlap":0.5199,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.4959,"overlap_user_count":418},{"event_a_id":8,"event_b_id":23,"score_user_overlap":0.5171,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.4943,"overlap_user_count":575},{"event_a_id":6,"event_b_id":15,"score_user_overlap":0.4701,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.4741,"overlap_user_count":425},{"event_a_id":2,"event_b_id":3,"score_user_overlap":0.5823,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.8,"score_composite":0.4734,"overlap_user_count":566},{"event_a_id":6,"event_b_id":18,"score_user_overlap":0.4758,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.4695,"overlap_user_count":432},{"event_a_id":6,"event_b_id":17,"score_user_overlap":0.4692,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.4655,"overlap_user_count":442},{"event_a_id":18,"event_b_id":24,"score_user_overlap":0.4605,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.4603,"overlap_user_count":425},{"event_a_id":12,"event_b_id":15,"score_user_overlap":0.6596,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4597,"overlap_user_count":558},{"event_a_id":17,"event_b_id":24,"score_user_overlap":0.4591,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.4595,"overlap_user_count":438},{"event_a_id":6,"event_b_id":11,"score_user_overlap":0.445,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.459,"overlap_user_count":433},{"event_a_id":6,"event_b_id":7,"score_user_overlap":0.5,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.452,"overlap_user_count":423},{"event_a_id":2,"event_b_id":15,"score_user_overlap":0.6433,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.45,"overlap_user_count":559},{"event_a_id":17,"event_b_id":18,"score_user_overlap":0.4272,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.4403,"overlap_user_count":452},{"event_a_id":8,"event_b_id":17,"score_user_overlap":0.4129,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.4397,"overlap_user_count":469},{"event_a_id":10,"event_b_id":17,"score_user_overlap":0.4103,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.4382,"overlap_user_count":471},{"event_a_id":9,"event_b_id":12,"score_user_overlap":0.6224,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4374,"overlap_user_count":562},{"event_a_id":7,"event_b_id":24,"score_user_overlap":0.4644,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.4307,"overlap_user_count":405},{"event_a_id":12,"event_b_id":19,"score_user_overlap":0.6086,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4291,"overlap_user_count":555},{"event_a_id":2,"event_b_id":9,"score_user_overlap":0.6063,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4278,"overlap_user_count":562},{"event_a_id":2,"event_b_id":11,"score_user_overlap":0.6062,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4277,"overlap_user_count":568},{"event_a_id":11,"event_b_id":12,"score_user_overlap":0.5994,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4236,"overlap_user_count":555},{"event_a_id":10,"event_b_id":12,"score_user_overlap":0.5975,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4225,"overlap_user_count":570},{"event_a_id":3,"event_b_id":12,"score_user_overlap":0.5937,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4202,"overlap_user_count":564},{"event_a_id":2,"event_b_id":19,"score_user_overlap":0.5929,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4198,"overlap_user_count":555},{"event_a_id":15,"event_b_id":24,"score_user_overlap":0.4454,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.4192,"overlap_user_count":412},{"event_a_id":15,"event_b_id":18,"score_user_overlap":0.4435,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.4181,"overlap_user_count":447},{"event_a_id":12,"event_b_id":14,"score_user_overlap":0.5881,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4169,"overlap_user_count":564},{"event_a_id":8,"event_b_id":12,"score_user_overlap":0.5878,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4167,"overlap_user_count":559},{"event_a_id":3,"event_b_id":6,"score_user_overlap":0.4376,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.4145,"overlap_user_count":438},{"event_a_id":7,"event_b_id":18,"score_user_overlap":0.4367,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.414,"overlap_user_count":424},{"event_a_id":2,"event_b_id":10,"score_user_overlap":0.5796,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4118,"overlap_user_count":568},{"event_a_id":3,"event_b_id":24,"score_user_overlap":0.4327,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.4116,"overlap_user_count":437},{"event_a_id":12,"event_b_id":23,"score_user_overlap":0.5757,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4094,"overlap_user_count":563},{"event_a_id":9,"event_b_id":24,"score_user_overlap":0.428,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.4088,"overlap_user_count":419},{"event_a_id":2,"event_b_id":14,"score_user_overlap":0.5722,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4073,"overlap_user_count":563},{"event_a_id":11,"event_b_id":24,"score_user_overlap":0.4254,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.4072,"overlap_user_count":422},{"event_a_id":2,"event_b_id":8,"score_user_overlap":0.5717,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.407,"overlap_user_count":558},{"event_a_id":7,"event_b_id":17,"score_user_overlap":0.4248,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.4069,"overlap_user_count":429},{"event_a_id":2,"event_b_id":23,"score_user_overlap":0.5681,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.8,"score_composite":0.4049,"overlap_user_count":567},{"event_a_id":14,"event_b_id":24,"score_user_overlap":0.4191,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.4035,"overlap_user_count":430},{"event_a_id":19,"event_b_id":24,"score_user_overlap":0.4184,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.4031,"overlap_user_count":413},{"event_a_id":11,"event_b_id":18,"score_user_overlap":0.4159,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.4015,"overlap_user_count":450},{"event_a_id":23,"event_b_id":24,"score_user_overlap":0.4132,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.3999,"overlap_user_count":431},{"event_a_id":8,"event_b_id":18,"score_user_overlap":0.4127,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.3996,"overlap_user_count":456},{"event_a_id":16,"event_b_id":26,"score_user_overlap":0.245,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.399,"overlap_user_count":172},{"event_a_id":8,"event_b_id":24,"score_user_overlap":0.4106,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.3983,"overlap_user_count":420},{"event_a_id":18,"event_b_id":23,"score_user_overlap":0.4088,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.3973,"overlap_user_count":462},{"event_a_id":5,"event_b_id":26,"score_user_overlap":0.2417,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.397,"overlap_user_count":174},{"event_a_id":10,"event_b_id":24,"score_user_overlap":0.4064,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.3958,"overlap_user_count":421},{"event_a_id":3,"event_b_id":17,"score_user_overlap":0.4052,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.3951,"overlap_user_count":464},{"event_a_id":14,"event_b_id":18,"score_user_overlap":0.4041,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.3945,"overlap_user_count":453},{"event_a_id":14,"event_b_id":17,"score_user_overlap":0.4033,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.394,"overlap_user_count":465},{"event_a_id":10,"event_b_id":18,"score_user_overlap":0.4025,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.3935,"overlap_user_count":452},{"event_a_id":5,"event_b_id":16,"score_user_overlap":0.227,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.3882,"overlap_user_count":178},{"event_a_id":17,"event_b_id":23,"score_user_overlap":0.39,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.386,"overlap_user_count":459},{"event_a_id":1,"event_b_id":16,"score_user_overlap":0.2517,"score_venue":1.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.383,"overlap_user_count":189},{"event_a_id":2,"event_b_id":6,"score_user_overlap":0.4803,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.3802,"overlap_user_count":426},{"event_a_id":6,"event_b_id":9,"score_user_overlap":0.454,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.3644,"overlap_user_count":434},{"event_a_id":2,"event_b_id":24,"score_user_overlap":0.4501,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.362,"overlap_user_count":410},{"event_a_id":6,"event_b_id":8,"score_user_overlap":0.448,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.3608,"overlap_user_count":444},{"event_a_id":6,"event_b_id":19,"score_user_overlap":0.441,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.3566,"overlap_user_count":426},{"event_a_id":1,"event_b_id":25,"score_user_overlap":0.2667,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.352,"overlap_user_count":164},{"event_a_id":2,"event_b_id":18,"score_user_overlap":0.4333,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.352,"overlap_user_count":435},{"event_a_id":6,"event_b_id":10,"score_user_overlap":0.4332,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.3519,"overlap_user_count":438},{"event_a_id":15,"event_b_id":17,"score_user_overlap":0.4142,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.3405,"overlap_user_count":439},{"event_a_id":2,"event_b_id":17,"score_user_overlap":0.4124,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.3394,"overlap_user_count":433},{"event_a_id":11,"event_b_id":17,"score_user_overlap":0.4009,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.3325,"overlap_user_count":451},{"event_a_id":9,"event_b_id":17,"score_user_overlap":0.3978,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.3307,"overlap_user_count":444},{"event_a_id":17,"event_b_id":19,"score_user_overlap":0.3909,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.4,"score_composite":0.3266,"overlap_user_count":439},{"event_a_id":25,"event_b_id":26,"score_user_overlap":0.3179,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.3228,"overlap_user_count":172},{"event_a_id":6,"event_b_id":12,"score_user_overlap":0.4765,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.3179,"overlap_user_count":416},{"event_a_id":5,"event_b_id":17,"score_user_overlap":0.1559,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.3135,"overlap_user_count":171},{"event_a_id":13,"event_b_id":27,"score_user_overlap":0.2143,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.8,"score_composite":0.3126,"overlap_user_count":105},{"event_a_id":1,"event_b_id":21,"score_user_overlap":0.1397,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.3038,"overlap_user_count":115},{"event_a_id":16,"event_b_id":17,"score_user_overlap":0.1387,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.3032,"overlap_user_count":152},{"event_a_id":12,"event_b_id":24,"score_user_overlap":0.4459,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.2996,"overlap_user_count":400},{"event_a_id":16,"event_b_id":25,"score_user_overlap":0.2782,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.2989,"overlap_user_count":170},{"event_a_id":17,"event_b_id":26,"score_user_overlap":0.1292,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.2975,"overlap_user_count":135},{"event_a_id":1,"event_b_id":20,"score_user_overlap":0.1234,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.294,"overlap_user_count":87},{"event_a_id":1,"event_b_id":26,"score_user_overlap":0.2656,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.2914,"overlap_user_count":183},{"event_a_id":20,"event_b_id":25,"score_user_overlap":0.1184,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.291,"overlap_user_count":67},{"event_a_id":12,"event_b_id":18,"score_user_overlap":0.4293,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.2896,"overlap_user_count":425},{"event_a_id":21,"event_b_id":25,"score_user_overlap":0.1144,"score_venue":0.5,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.2887,"overlap_user_count":80},{"event_a_id":4,"event_b_id":26,"score_user_overlap":0.2257,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.2874,"overlap_user_count":144},{"event_a_id":5,"event_b_id":25,"score_user_overlap":0.2516,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.2829,"overlap_user_count":161},{"event_a_id":20,"event_b_id":22,"score_user_overlap":0.2161,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.2817,"overlap_user_count":94},{"event_a_id":12,"event_b_id":17,"score_user_overlap":0.4069,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.2762,"overlap_user_count":422},{"event_a_id":4,"event_b_id":5,"score_user_overlap":0.1983,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.271,"overlap_user_count":144},{"event_a_id":1,"event_b_id":5,"score_user_overlap":0.2308,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.2705,"overlap_user_count":180},{"event_a_id":4,"event_b_id":16,"score_user_overlap":0.1921,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.2673,"overlap_user_count":137},{"event_a_id":21,"event_b_id":22,"score_user_overlap":0.1863,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.4,"score_composite":0.2638,"overlap_user_count":106},{"event_a_id":5,"event_b_id":10,"score_user_overlap":0.1413,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.2448,"overlap_user_count":165},{"event_a_id":10,"event_b_id":16,"score_user_overlap":0.1398,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.2439,"overlap_user_count":161},{"event_a_id":8,"event_b_id":16,"score_user_overlap":0.1385,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.2431,"overlap_user_count":158},{"event_a_id":5,"event_b_id":8,"score_user_overlap":0.1351,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.2411,"overlap_user_count":157},{"event_a_id":10,"event_b_id":26,"score_user_overlap":0.1277,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.2366,"overlap_user_count":141},{"event_a_id":8,"event_b_id":26,"score_user_overlap":0.1263,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.2358,"overlap_user_count":138},{"event_a_id":3,"event_b_id":13,"score_user_overlap":0.1166,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.23,"overlap_user_count":123},{"event_a_id":13,"event_b_id":18,"score_user_overlap":0.1078,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.2247,"overlap_user_count":105},{"event_a_id":3,"event_b_id":5,"score_user_overlap":0.1366,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.202,"overlap_user_count":159},{"event_a_id":16,"event_b_id":18,"score_user_overlap":0.1337,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.2002,"overlap_user_count":142},{"event_a_id":24,"event_b_id":27,"score_user_overlap":0.0654,"score_venue":0.5,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1992,"overlap_user_count":53},{"event_a_id":5,"event_b_id":18,"score_user_overlap":0.1292,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1975,"overlap_user_count":140},{"event_a_id":5,"event_b_id":24,"score_user_overlap":0.1274,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1965,"overlap_user_count":125},{"event_a_id":3,"event_b_id":16,"score_user_overlap":0.1252,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1951,"overlap_user_count":145},{"event_a_id":2,"event_b_id":5,"score_user_overlap":0.125,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.195,"overlap_user_count":133},{"event_a_id":14,"event_b_id":16,"score_user_overlap":0.1233,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.194,"overlap_user_count":144},{"event_a_id":4,"event_b_id":17,"score_user_overlap":0.1223,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1934,"overlap_user_count":126},{"event_a_id":2,"event_b_id":13,"score_user_overlap":0.1215,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1929,"overlap_user_count":114},{"event_a_id":3,"event_b_id":26,"score_user_overlap":0.1197,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1918,"overlap_user_count":132},{"event_a_id":5,"event_b_id":6,"score_user_overlap":0.1181,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1909,"overlap_user_count":116},{"event_a_id":16,"event_b_id":23,"score_user_overlap":0.1167,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.19,"overlap_user_count":139},{"event_a_id":7,"event_b_id":16,"score_user_overlap":0.1163,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1898,"overlap_user_count":118},{"event_a_id":24,"event_b_id":26,"score_user_overlap":0.1138,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1883,"overlap_user_count":104},{"event_a_id":12,"event_b_id":13,"score_user_overlap":0.1126,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1875,"overlap_user_count":104},{"event_a_id":16,"event_b_id":24,"score_user_overlap":0.1116,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1869,"overlap_user_count":109},{"event_a_id":18,"event_b_id":26,"score_user_overlap":0.1105,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1863,"overlap_user_count":113},{"event_a_id":1,"event_b_id":17,"score_user_overlap":0.1431,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1859,"overlap_user_count":156},{"event_a_id":17,"event_b_id":21,"score_user_overlap":0.1431,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1859,"overlap_user_count":156},{"event_a_id":6,"event_b_id":16,"score_user_overlap":0.1091,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1854,"overlap_user_count":106},{"event_a_id":6,"event_b_id":26,"score_user_overlap":0.1062,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1837,"overlap_user_count":97},{"event_a_id":2,"event_b_id":26,"score_user_overlap":0.1035,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1821,"overlap_user_count":104},{"event_a_id":22,"event_b_id":27,"score_user_overlap":0.2466,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.1799,"overlap_user_count":90},{"event_a_id":1,"event_b_id":10,"score_user_overlap":0.1321,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1793,"overlap_user_count":153},{"event_a_id":2,"event_b_id":4,"score_user_overlap":0.0982,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1789,"overlap_user_count":97},{"event_a_id":16,"event_b_id":21,"score_user_overlap":0.1312,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1787,"overlap_user_count":109},{"event_a_id":10,"event_b_id":21,"score_user_overlap":0.1302,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1781,"overlap_user_count":151},{"event_a_id":5,"event_b_id":13,"score_user_overlap":0.0941,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1765,"overlap_user_count":72},{"event_a_id":10,"event_b_id":20,"score_user_overlap":0.1256,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1754,"overlap_user_count":130},{"event_a_id":5,"event_b_id":21,"score_user_overlap":0.1254,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1753,"overlap_user_count":107},{"event_a_id":8,"event_b_id":21,"score_user_overlap":0.1249,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1749,"overlap_user_count":144},{"event_a_id":20,"event_b_id":26,"score_user_overlap":0.1238,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1743,"overlap_user_count":80},{"event_a_id":1,"event_b_id":8,"score_user_overlap":0.1229,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1738,"overlap_user_count":142},{"event_a_id":17,"event_b_id":27,"score_user_overlap":0.0892,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1735,"overlap_user_count":84},{"event_a_id":5,"event_b_id":27,"score_user_overlap":0.085,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.171,"overlap_user_count":58},{"event_a_id":4,"event_b_id":6,"score_user_overlap":0.0847,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1708,"overlap_user_count":77},{"event_a_id":16,"event_b_id":27,"score_user_overlap":0.0843,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1706,"overlap_user_count":56},{"event_a_id":5,"event_b_id":20,"score_user_overlap":0.1166,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.17,"overlap_user_count":85},{"event_a_id":16,"event_b_id":20,"score_user_overlap":0.1167,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.17,"overlap_user_count":83},{"event_a_id":21,"event_b_id":26,"score_user_overlap":0.1165,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1699,"overlap_user_count":91},{"event_a_id":17,"event_b_id":25,"score_user_overlap":0.116,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1696,"overlap_user_count":113},{"event_a_id":13,"event_b_id":26,"score_user_overlap":0.0824,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1694,"overlap_user_count":57},{"event_a_id":4,"event_b_id":25,"score_user_overlap":0.2282,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.1689,"overlap_user_count":128},{"event_a_id":9,"event_b_id":13,"score_user_overlap":0.1112,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1667,"overlap_user_count":113},{"event_a_id":26,"event_b_id":27,"score_user_overlap":0.0777,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1666,"overlap_user_count":47},{"event_a_id":8,"event_b_id":25,"score_user_overlap":0.1092,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1655,"overlap_user_count":112},{"event_a_id":8,"event_b_id":20,"score_user_overlap":0.1089,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1653,"overlap_user_count":113},{"event_a_id":17,"event_b_id":20,"score_user_overlap":0.1089,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1653,"overlap_user_count":108},{"event_a_id":6,"event_b_id":27,"score_user_overlap":0.0754,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1652,"overlap_user_count":60},{"event_a_id":13,"event_b_id":22,"score_user_overlap":0.2212,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.1647,"overlap_user_count":100},{"event_a_id":2,"event_b_id":27,"score_user_overlap":0.0742,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1645,"overlap_user_count":66},{"event_a_id":10,"event_b_id":25,"score_user_overlap":0.1066,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.164,"overlap_user_count":111},{"event_a_id":4,"event_b_id":13,"score_user_overlap":0.0725,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1635,"overlap_user_count":49},{"event_a_id":20,"event_b_id":27,"score_user_overlap":0.2144,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.1607,"overlap_user_count":101},{"event_a_id":4,"event_b_id":27,"score_user_overlap":0.0644,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1586,"overlap_user_count":38},{"event_a_id":13,"event_b_id":19,"score_user_overlap":0.0959,"score_venue":0.5,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.1576,"overlap_user_count":99},{"event_a_id":1,"event_b_id":4,"score_user_overlap":0.2063,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.1558,"overlap_user_count":145},{"event_a_id":22,"event_b_id":25,"score_user_overlap":0.0488,"score_venue":0.0,"score_temporal":1.0,"score_organizer":0.0,"score_composite":0.1493,"overlap_user_count":24},{"event_a_id":13,"event_b_id":20,"score_user_overlap":0.1946,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.1488,"overlap_user_count":109},{"event_a_id":5,"event_b_id":23,"score_user_overlap":0.1402,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1441,"overlap_user_count":166},{"event_a_id":5,"event_b_id":15,"score_user_overlap":0.1368,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1421,"overlap_user_count":146},{"event_a_id":5,"event_b_id":11,"score_user_overlap":0.1366,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1419,"overlap_user_count":155},{"event_a_id":5,"event_b_id":19,"score_user_overlap":0.1342,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1405,"overlap_user_count":151},{"event_a_id":5,"event_b_id":9,"score_user_overlap":0.1335,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1401,"overlap_user_count":150},{"event_a_id":5,"event_b_id":14,"score_user_overlap":0.1327,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1396,"overlap_user_count":156},{"event_a_id":21,"event_b_id":27,"score_user_overlap":0.179,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.1394,"overlap_user_count":109},{"event_a_id":5,"event_b_id":12,"score_user_overlap":0.1322,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1393,"overlap_user_count":137},{"event_a_id":5,"event_b_id":7,"score_user_overlap":0.1293,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1376,"overlap_user_count":132},{"event_a_id":11,"event_b_id":16,"score_user_overlap":0.1249,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1349,"overlap_user_count":141},{"event_a_id":16,"event_b_id":19,"score_user_overlap":0.1204,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1323,"overlap_user_count":135},{"event_a_id":13,"event_b_id":21,"score_user_overlap":0.1643,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.4,"score_composite":0.1306,"overlap_user_count":115},{"event_a_id":13,"event_b_id":17,"score_user_overlap":0.1174,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1304,"overlap_user_count":118},{"event_a_id":11,"event_b_id":26,"score_user_overlap":0.1171,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1303,"overlap_user_count":126},{"event_a_id":15,"event_b_id":16,"score_user_overlap":0.1139,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1283,"overlap_user_count":122},{"event_a_id":13,"event_b_id":24,"score_user_overlap":0.1136,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1281,"overlap_user_count":98},{"event_a_id":12,"event_b_id":26,"score_user_overlap":0.1128,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1277,"overlap_user_count":110},{"event_a_id":19,"event_b_id":26,"score_user_overlap":0.1113,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1268,"overlap_user_count":119},{"event_a_id":9,"event_b_id":16,"score_user_overlap":0.1107,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1264,"overlap_user_count":125},{"event_a_id":9,"event_b_id":26,"score_user_overlap":0.1105,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1263,"overlap_user_count":118},{"event_a_id":15,"event_b_id":26,"score_user_overlap":0.1095,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1257,"overlap_user_count":111},{"event_a_id":23,"event_b_id":26,"score_user_overlap":0.109,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1254,"overlap_user_count":124},{"event_a_id":1,"event_b_id":12,"score_user_overlap":0.1089,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1253,"overlap_user_count":113},{"event_a_id":7,"event_b_id":26,"score_user_overlap":0.1082,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1249,"overlap_user_count":104},{"event_a_id":3,"event_b_id":4,"score_user_overlap":0.108,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1248,"overlap_user_count":118},{"event_a_id":14,"event_b_id":26,"score_user_overlap":0.1077,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1246,"overlap_user_count":121},{"event_a_id":2,"event_b_id":16,"score_user_overlap":0.1072,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1243,"overlap_user_count":114},{"event_a_id":6,"event_b_id":13,"score_user_overlap":0.1056,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1233,"overlap_user_count":91},{"event_a_id":4,"event_b_id":7,"score_user_overlap":0.1028,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1217,"overlap_user_count":97},{"event_a_id":4,"event_b_id":23,"score_user_overlap":0.0995,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1197,"overlap_user_count":112},{"event_a_id":4,"event_b_id":14,"score_user_overlap":0.0991,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1195,"overlap_user_count":110},{"event_a_id":4,"event_b_id":12,"score_user_overlap":0.0983,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.119,"overlap_user_count":95},{"event_a_id":4,"event_b_id":24,"score_user_overlap":0.0935,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1161,"overlap_user_count":85},{"event_a_id":13,"event_b_id":16,"score_user_overlap":0.0893,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1136,"overlap_user_count":67},{"event_a_id":4,"event_b_id":18,"score_user_overlap":0.0881,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1128,"overlap_user_count":90},{"event_a_id":18,"event_b_id":27,"score_user_overlap":0.0851,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.111,"overlap_user_count":77},{"event_a_id":12,"event_b_id":27,"score_user_overlap":0.0826,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1095,"overlap_user_count":71},{"event_a_id":3,"event_b_id":27,"score_user_overlap":0.0799,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.108,"overlap_user_count":80},{"event_a_id":14,"event_b_id":27,"score_user_overlap":0.0771,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1062,"overlap_user_count":78},{"event_a_id":23,"event_b_id":27,"score_user_overlap":0.0736,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1042,"overlap_user_count":76},{"event_a_id":7,"event_b_id":27,"score_user_overlap":0.073,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.1038,"overlap_user_count":62},{"event_a_id":1,"event_b_id":22,"score_user_overlap":0.0547,"score_venue":0.0,"score_temporal":0.5,"score_organizer":0.0,"score_composite":0.0928,"overlap_user_count":35},{"event_a_id":18,"event_b_id":21,"score_user_overlap":0.1361,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0817,"overlap_user_count":144},{"event_a_id":21,"event_b_id":24,"score_user_overlap":0.1268,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0761,"overlap_user_count":122},{"event_a_id":9,"event_b_id":21,"score_user_overlap":0.1249,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0749,"overlap_user_count":139},{"event_a_id":19,"event_b_id":21,"score_user_overlap":0.1237,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0742,"overlap_user_count":138},{"event_a_id":12,"event_b_id":16,"score_user_overlap":0.1227,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0736,"overlap_user_count":126},{"event_a_id":10,"event_b_id":13,"score_user_overlap":0.1218,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0731,"overlap_user_count":129},{"event_a_id":13,"event_b_id":15,"score_user_overlap":0.1218,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0731,"overlap_user_count":116},{"event_a_id":11,"event_b_id":13,"score_user_overlap":0.1204,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0722,"overlap_user_count":123},{"event_a_id":13,"event_b_id":14,"score_user_overlap":0.1198,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0719,"overlap_user_count":127},{"event_a_id":4,"event_b_id":8,"score_user_overlap":0.1197,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0718,"overlap_user_count":129},{"event_a_id":8,"event_b_id":13,"score_user_overlap":0.1181,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0709,"overlap_user_count":124},{"event_a_id":1,"event_b_id":23,"score_user_overlap":0.1169,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0701,"overlap_user_count":139},{"event_a_id":1,"event_b_id":3,"score_user_overlap":0.1167,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.07,"overlap_user_count":136},{"event_a_id":3,"event_b_id":21,"score_user_overlap":0.1167,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.07,"overlap_user_count":136},{"event_a_id":6,"event_b_id":21,"score_user_overlap":0.115,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.069,"overlap_user_count":111},{"event_a_id":1,"event_b_id":24,"score_user_overlap":0.1141,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0684,"overlap_user_count":111},{"event_a_id":7,"event_b_id":21,"score_user_overlap":0.1132,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0679,"overlap_user_count":115},{"event_a_id":12,"event_b_id":21,"score_user_overlap":0.1132,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0679,"overlap_user_count":117},{"event_a_id":15,"event_b_id":21,"score_user_overlap":0.1131,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0679,"overlap_user_count":121},{"event_a_id":4,"event_b_id":10,"score_user_overlap":0.113,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0678,"overlap_user_count":124},{"event_a_id":14,"event_b_id":21,"score_user_overlap":0.113,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0678,"overlap_user_count":133},{"event_a_id":1,"event_b_id":18,"score_user_overlap":0.1119,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0672,"overlap_user_count":121},{"event_a_id":1,"event_b_id":15,"score_user_overlap":0.111,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0666,"overlap_user_count":119},{"event_a_id":1,"event_b_id":19,"score_user_overlap":0.1107,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0664,"overlap_user_count":125},{"event_a_id":1,"event_b_id":14,"score_user_overlap":0.1102,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0661,"overlap_user_count":130},{"event_a_id":4,"event_b_id":19,"score_user_overlap":0.1096,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0658,"overlap_user_count":115},{"event_a_id":13,"event_b_id":23,"score_user_overlap":0.1096,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0657,"overlap_user_count":119},{"event_a_id":1,"event_b_id":6,"score_user_overlap":0.1093,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0656,"overlap_user_count":106},{"event_a_id":11,"event_b_id":21,"score_user_overlap":0.1094,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0656,"overlap_user_count":125},{"event_a_id":2,"event_b_id":21,"score_user_overlap":0.1085,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0651,"overlap_user_count":115},{"event_a_id":21,"event_b_id":23,"score_user_overlap":0.1085,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0651,"overlap_user_count":130},{"event_a_id":1,"event_b_id":9,"score_user_overlap":0.108,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0648,"overlap_user_count":122},{"event_a_id":7,"event_b_id":13,"score_user_overlap":0.1077,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0646,"overlap_user_count":98},{"event_a_id":19,"event_b_id":20,"score_user_overlap":0.1058,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0635,"overlap_user_count":106},{"event_a_id":1,"event_b_id":11,"score_user_overlap":0.1055,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0633,"overlap_user_count":121},{"event_a_id":1,"event_b_id":7,"score_user_overlap":0.1045,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0627,"overlap_user_count":107},{"event_a_id":9,"event_b_id":20,"score_user_overlap":0.1038,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0623,"overlap_user_count":104},{"event_a_id":4,"event_b_id":9,"score_user_overlap":0.1035,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0621,"overlap_user_count":109},{"event_a_id":3,"event_b_id":20,"score_user_overlap":0.1032,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0619,"overlap_user_count":108},{"event_a_id":1,"event_b_id":2,"score_user_overlap":0.1023,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0614,"overlap_user_count":109},{"event_a_id":3,"event_b_id":25,"score_user_overlap":0.1023,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0614,"overlap_user_count":106},{"event_a_id":18,"event_b_id":20,"score_user_overlap":0.1023,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0614,"overlap_user_count":98},{"event_a_id":12,"event_b_id":25,"score_user_overlap":0.101,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0606,"overlap_user_count":91},{"event_a_id":7,"event_b_id":25,"score_user_overlap":0.1008,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0605,"overlap_user_count":89},{"event_a_id":23,"event_b_id":25,"score_user_overlap":0.1008,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0605,"overlap_user_count":107},{"event_a_id":2,"event_b_id":20,"score_user_overlap":0.1005,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0603,"overlap_user_count":94},{"event_a_id":4,"event_b_id":11,"score_user_overlap":0.0999,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0599,"overlap_user_count":107},{"event_a_id":12,"event_b_id":20,"score_user_overlap":0.0984,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.059,"overlap_user_count":90},{"event_a_id":4,"event_b_id":20,"score_user_overlap":0.0969,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0581,"overlap_user_count":62},{"event_a_id":15,"event_b_id":20,"score_user_overlap":0.0965,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0579,"overlap_user_count":92},{"event_a_id":20,"event_b_id":23,"score_user_overlap":0.0965,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0579,"overlap_user_count":104},{"event_a_id":19,"event_b_id":25,"score_user_overlap":0.0961,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0577,"overlap_user_count":96},{"event_a_id":14,"event_b_id":20,"score_user_overlap":0.096,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0576,"overlap_user_count":102},{"event_a_id":11,"event_b_id":25,"score_user_overlap":0.0958,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0575,"overlap_user_count":97},{"event_a_id":4,"event_b_id":21,"score_user_overlap":0.0956,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0574,"overlap_user_count":74},{"event_a_id":15,"event_b_id":25,"score_user_overlap":0.0955,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0573,"overlap_user_count":90},{"event_a_id":14,"event_b_id":25,"score_user_overlap":0.0951,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0571,"overlap_user_count":100},{"event_a_id":6,"event_b_id":20,"score_user_overlap":0.0941,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0565,"overlap_user_count":80},{"event_a_id":20,"event_b_id":24,"score_user_overlap":0.0932,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0559,"overlap_user_count":80},{"event_a_id":9,"event_b_id":25,"score_user_overlap":0.093,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0558,"overlap_user_count":93},{"event_a_id":25,"event_b_id":27,"score_user_overlap":0.0918,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0551,"overlap_user_count":47},{"event_a_id":6,"event_b_id":25,"score_user_overlap":0.0917,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.055,"overlap_user_count":77},{"event_a_id":11,"event_b_id":20,"score_user_overlap":0.0914,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0549,"overlap_user_count":94},{"event_a_id":4,"event_b_id":15,"score_user_overlap":0.0912,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0547,"overlap_user_count":92},{"event_a_id":8,"event_b_id":27,"score_user_overlap":0.0912,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0547,"overlap_user_count":90},{"event_a_id":1,"event_b_id":13,"score_user_overlap":0.091,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0546,"overlap_user_count":68},{"event_a_id":7,"event_b_id":20,"score_user_overlap":0.0908,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0545,"overlap_user_count":82},{"event_a_id":10,"event_b_id":27,"score_user_overlap":0.0899,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0539,"overlap_user_count":90},{"event_a_id":2,"event_b_id":25,"score_user_overlap":0.089,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0534,"overlap_user_count":83},{"event_a_id":18,"event_b_id":25,"score_user_overlap":0.0876,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0526,"overlap_user_count":84},{"event_a_id":24,"event_b_id":25,"score_user_overlap":0.087,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0522,"overlap_user_count":74},{"event_a_id":9,"event_b_id":27,"score_user_overlap":0.0795,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0477,"overlap_user_count":76},{"event_a_id":19,"event_b_id":27,"score_user_overlap":0.0782,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0469,"overlap_user_count":75},{"event_a_id":13,"event_b_id":25,"score_user_overlap":0.0754,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0452,"overlap_user_count":46},{"event_a_id":11,"event_b_id":27,"score_user_overlap":0.0738,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0443,"overlap_user_count":72},{"event_a_id":15,"event_b_id":27,"score_user_overlap":0.0729,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0438,"overlap_user_count":66},{"event_a_id":17,"event_b_id":22,"score_user_overlap":0.0708,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0425,"overlap_user_count":65},{"event_a_id":10,"event_b_id":22,"score_user_overlap":0.0705,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0423,"overlap_user_count":69},{"event_a_id":22,"event_b_id":24,"score_user_overlap":0.0704,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0422,"overlap_user_count":54},{"event_a_id":15,"event_b_id":22,"score_user_overlap":0.0691,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0415,"overlap_user_count":60},{"event_a_id":1,"event_b_id":27,"score_user_overlap":0.0685,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0411,"overlap_user_count":46},{"event_a_id":18,"event_b_id":22,"score_user_overlap":0.0683,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.041,"overlap_user_count":60},{"event_a_id":8,"event_b_id":22,"score_user_overlap":0.0671,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0402,"overlap_user_count":65},{"event_a_id":12,"event_b_id":22,"score_user_overlap":0.066,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0396,"overlap_user_count":55},{"event_a_id":9,"event_b_id":22,"score_user_overlap":0.0657,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0394,"overlap_user_count":61},{"event_a_id":3,"event_b_id":22,"score_user_overlap":0.0646,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0388,"overlap_user_count":63},{"event_a_id":19,"event_b_id":22,"score_user_overlap":0.0644,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0387,"overlap_user_count":60},{"event_a_id":11,"event_b_id":22,"score_user_overlap":0.0624,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0374,"overlap_user_count":59},{"event_a_id":14,"event_b_id":22,"score_user_overlap":0.0619,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0371,"overlap_user_count":61},{"event_a_id":22,"event_b_id":23,"score_user_overlap":0.0618,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0371,"overlap_user_count":62},{"event_a_id":2,"event_b_id":22,"score_user_overlap":0.0617,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.037,"overlap_user_count":53},{"event_a_id":7,"event_b_id":22,"score_user_overlap":0.0585,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0351,"overlap_user_count":48},{"event_a_id":16,"event_b_id":22,"score_user_overlap":0.0562,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0337,"overlap_user_count":36},{"event_a_id":4,"event_b_id":22,"score_user_overlap":0.056,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0336,"overlap_user_count":31},{"event_a_id":6,"event_b_id":22,"score_user_overlap":0.0545,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0327,"overlap_user_count":42},{"event_a_id":22,"event_b_id":26,"score_user_overlap":0.05,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.03,"overlap_user_count":29},{"event_a_id":5,"event_b_id":22,"score_user_overlap":0.0497,"score_venue":0.0,"score_temporal":0.0,"score_organizer":0.0,"score_composite":0.0298,"overlap_user_count":33}]};

const EVENTS = DB.events;
const SIM_INDEX = (() => {
  const idx = {};
  for (const s of DB.similarity) {
    const { event_a_id: a, event_b_id: b, ...scores } = s;
    if (!idx[a]) idx[a] = {};
    if (!idx[b]) idx[b] = {};
    idx[a][b] = scores;
    idx[b][a] = scores;
  }
  return idx;
})();

// ── Helpers ────────────────────────────────────────────────────────────────
const TODAY = new Date().toISOString().slice(0, 10);

const SOURCE_META = {
  secret_tel_aviv:      { label: "Secret TLV",  color: "#e879f9" },
  entrio:               { label: "Entrio",       color: "#6366f1" },
  bandsintown:          { label: "Bandsintown",  color: "#22c55e" },
  tel_aviv_municipality:{ label: "TLV City",     color: "#a855f7" },
  eventbrite:           { label: "Eventbrite",   color: "#f97316" },
};

const CAT_EMOJI = {
  music:    { dj_set:"🎧", live:"🎸", festival:"🎪", default:"🎵" },
  cultural: { exhibition:"🖼️", tour:"🏛️", film:"🎬", pride:"🏳️‍🌈", festival:"🎉", default:"✨" },
  market:   { food:"🍽️", crafts:"🛍️", flea:"🪴", default:"🏪" },
};

function getEmoji(ev) {
  const catMap = CAT_EMOJI[ev.category] || {};
  const sub = (ev.subcategory || "").replace("-","_");
  return catMap[sub] || catMap.default || "📌";
}

function fmtDate(d) {
  if (!d) return "";
  const dt = new Date(d + "T00:00:00");
  const days = Math.round((dt - new Date(TODAY + "T00:00:00")) / 86400000);
  if (days === 0) return "Today";
  if (days === 1) return "Tomorrow";
  return dt.toLocaleDateString("en-IL", { weekday:"short", month:"short", day:"numeric" });
}

function fmtPrice(ev) {
  if (ev.price_min === 0 && !ev.price_max) return "Free";
  if (ev.price_min === 0 && ev.price_max === 0) return "Free";
  if (ev.price_max && ev.price_max !== ev.price_min) return `₪${ev.price_min}–${ev.price_max}`;
  return `₪${ev.price_min}`;
}

function getSimilar(events, eventId, n = 5) {
  const row = SIM_INDEX[eventId] || {};
  return events
    .filter(e => e.id !== eventId && row[e.id])
    .sort((a,b) => row[b.id].score_composite - row[a.id].score_composite)
    .slice(0, n)
    .map(e => ({ ...e, _sim: row[e.id] }));
}

function matchDate(ev, filter, dateRange) {
  if (dateRange?.start) {
    if (dateRange.end) return ev.event_date >= dateRange.start && ev.event_date <= dateRange.end;
    return ev.event_date === dateRange.start;
  }
  if (filter === "all") return true;
  const diff = Math.round((new Date(ev.event_date+"T00:00:00") - new Date(TODAY+"T00:00:00")) / 86400000);
  if (filter === "today")     return diff === 0;
  if (filter === "tomorrow")  return diff === 1;
  if (filter === "weekend")   return diff >= 0 && diff <= 7;
  if (filter === "next-week") return diff >= 7 && diff <= 14;
  return true;
}

// ── Style tokens ──────────────────────────────────────────────────────────
const T = {
  bg0: "#080e0e", bg1: "#0e1a1a", bg2: "#142020", border: "#1e3030",
  borderHover: "#2e5050", amber: "#F5A623", amberDim: "rgba(245,166,35,0.12)",
  teal: "#1A3A4A", tealBright: "#7ecef5", text: "#F0EDE6", textMid: "#8ba0a0",
  textDim: "#4a6060", green: "#22c55e", font: "'Syne',sans-serif", body: "'Inter',sans-serif",
};

// ── Components ─────────────────────────────────────────────────────────────

function PulseRing() {
  return <span style={{ display:"inline-block", width:8, height:8, borderRadius:"50%", background:T.amber, animation:"pulse 1.8s infinite", marginRight:6, verticalAlign:"middle" }} />;
}

function Badge({ source }) {
  const m = SOURCE_META[source] || { label:source, color:"#8ba0a0" };
  return <span style={{ fontSize:9, fontFamily:T.font, fontWeight:700, color:m.color, background:m.color+"18", padding:"2px 6px", borderRadius:3, letterSpacing:"0.05em" }}>{m.label}</span>;
}

function Tag({ label }) {
  return <span style={{ fontSize:9, fontFamily:T.body, color:T.textMid, background:T.bg2, padding:"2px 7px", borderRadius:3 }}>{label}</span>;
}

function ScoreBar({ label, value, color }) {
  return (
    <div style={{ marginBottom:5 }}>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:2 }}>
        <span style={{ fontSize:10, color:T.textDim, fontFamily:T.body }}>{label}</span>
        <span style={{ fontSize:10, color, fontFamily:T.font, fontWeight:700 }}>{Math.round(value*100)}%</span>
      </div>
      <div style={{ height:2, background:T.border, borderRadius:1 }}>
        <div style={{ height:2, width:`${value*100}%`, background:color, borderRadius:1 }} />
      </div>
    </div>
  );
}

function EventCard({ ev, onClick, compact }) {
  const isToday = ev.event_date === TODAY;
  const emoji = getEmoji(ev);
  const [hover, setHover] = useState(false);

  return (
    <div
      onClick={() => onClick(ev)}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: T.bg1, borderRadius:12, padding: compact ? "14px 16px" : "18px 20px",
        border: `1px solid ${isToday ? "rgba(245,166,35,0.35)" : hover ? T.borderHover : T.border}`,
        cursor:"pointer", position:"relative", overflow:"hidden",
        transform: hover ? "translateY(-2px)" : "none",
        transition:"transform 0.15s, border-color 0.15s",
      }}
    >
      {isToday && (
        <div style={{ position:"absolute", top:0, right:0, background:"rgba(245,166,35,0.1)", borderBottomLeftRadius:8, padding:"3px 10px", fontSize:9, color:T.amber, fontFamily:T.font, fontWeight:700, letterSpacing:"0.08em", display:"flex", alignItems:"center" }}>
          <PulseRing />TODAY
        </div>
      )}

      <div style={{ fontSize: compact ? 24 : 30, marginBottom:10 }}>{emoji}</div>

      <div style={{ fontFamily:T.font, fontSize: compact ? 14 : 15, fontWeight:700, color:T.text, lineHeight:1.3, marginBottom:5, paddingRight: isToday ? 70 : 0 }}>
        {ev.title}
      </div>

      <div style={{ fontSize:11, color:T.textDim, fontFamily:T.body, marginBottom:10 }}>
        {ev.venue_name}{ev.neighborhood ? ` · ${ev.neighborhood}` : ""}
      </div>

      {!compact && ev.tags?.length > 0 && (
        <div style={{ display:"flex", gap:4, flexWrap:"wrap", marginBottom:10 }}>
          {ev.tags.slice(0,3).map(t => <Tag key={t} label={t} />)}
        </div>
      )}

      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-end" }}>
        <div>
          <div style={{ fontFamily:T.font, fontSize:12, color:T.amber, fontWeight:600 }}>
            {fmtDate(ev.event_date)}{ev.start_time ? ` · ${ev.start_time}` : ""}
          </div>
          {!compact && <div style={{ marginTop:5 }}><Badge source={ev.source} /></div>}
        </div>
        <div style={{ fontFamily:T.font, fontSize: compact ? 13 : 15, fontWeight:700, color: ev.price_min===0 ? T.green : T.text }}>
          {fmtPrice(ev)}
        </div>
      </div>
    </div>
  );
}

function SimilarMini({ ev, onClick }) {
  const pct = Math.round((ev._sim?.score_composite || 0) * 100);
  const sim = ev._sim || {};
  const topSignal =
    sim.score_user_overlap > 0.12 ? { icon:"👥", label:"Shared crowd", c:"#6366f1" } :
    sim.score_venue > 0.4         ? { icon:"📍", label:"Same venue",   c:"#22c55e" } :
    sim.score_temporal > 0.4      ? { icon:"🕐", label:"Same timeslot",c:"#0ea5e9" } :
                                    { icon:"🎭", label:"Same scene",   c:"#a855f7" };
  const [hover, setHover] = useState(false);

  return (
    <div
      onClick={() => onClick(ev)}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        minWidth:188, maxWidth:188, background:T.bg0,
        border:`1px solid ${hover ? T.amber : T.border}`,
        borderRadius:10, padding:"13px 14px", cursor:"pointer", flexShrink:0,
        transform: hover ? "translateY(-2px)" : "none",
        transition:"all 0.15s", position:"relative",
      }}
    >
      <div style={{ position:"absolute", top:8, right:8, background: pct>=55 ? T.amberDim : T.bg2, border:`1px solid ${pct>=55 ? "rgba(245,166,35,0.4)" : T.border}`, borderRadius:5, padding:"1px 6px", fontSize:10, fontFamily:T.font, fontWeight:700, color: pct>=55 ? T.amber : T.textDim }}>
        {pct}%
      </div>
      <div style={{ fontSize:20, marginBottom:7 }}>{getEmoji(ev)}</div>
      <div style={{ fontFamily:T.font, fontSize:12, fontWeight:700, color:T.text, lineHeight:1.3, marginBottom:3, paddingRight:32 }}>{ev.title}</div>
      <div style={{ fontSize:10, color:T.textDim, fontFamily:T.body, marginBottom:8 }}>{ev.venue_name}</div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
        <span style={{ fontSize:10, color:T.amber, fontFamily:T.font, fontWeight:600 }}>{fmtDate(ev.event_date)}</span>
        <span style={{ fontSize:11, color: ev.price_min===0 ? T.green : T.textMid, fontFamily:T.font, fontWeight:600 }}>{fmtPrice(ev)}</span>
      </div>
      <div style={{ borderTop:`1px solid ${T.border}`, paddingTop:7 }}>
        <span style={{ fontSize:9, color:topSignal.c, fontFamily:T.body, fontWeight:600 }}>{topSignal.icon} {topSignal.label}</span>
      </div>
    </div>
  );
}

function Modal({ ev, events, onClose, onNavigate }) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [pinned, setPinned] = useState(null);
  const similar = useMemo(() => getSimilar(events, ev.id), [events, ev.id]);
  const emoji = getEmoji(ev);

  useEffect(() => { setPinned(null); setShowBreakdown(false); }, [ev.id]);

  return (
    <div onClick={onClose} style={{ position:"fixed", inset:0, background:"rgba(0,0,0,0.8)", backdropFilter:"blur(10px)", zIndex:200, display:"flex", alignItems:"center", justifyContent:"center", padding:16 }}>
      <div onClick={e=>e.stopPropagation()} style={{ background:T.bg1, border:`1px solid ${T.border}`, borderRadius:18, maxWidth:520, width:"100%", maxHeight:"92vh", overflowY:"auto", position:"relative" }}>

        {/* ── Event info ── */}
        <div style={{ padding:"28px 28px 22px" }}>
          <button onClick={onClose} style={{ position:"absolute", top:14, right:14, background:"none", border:"none", color:T.textDim, fontSize:18, cursor:"pointer", lineHeight:1, padding:4 }}>✕</button>

          <div style={{ fontSize:42, marginBottom:14 }}>{emoji}</div>
          <div style={{ fontFamily:T.font, fontSize:20, fontWeight:700, color:T.text, lineHeight:1.25, marginBottom:8 }}>{ev.title}</div>

          {ev.event_date === TODAY && <div style={{ display:"flex", alignItems:"center", marginBottom:12 }}><PulseRing /><span style={{ color:T.amber, fontSize:10, fontFamily:T.font, fontWeight:700, letterSpacing:"0.08em" }}>HAPPENING TODAY</span></div>}

          {ev.description && <div style={{ fontFamily:T.body, fontSize:13, color:T.textMid, marginBottom:16, lineHeight:1.6 }}>{ev.description}</div>}

          <div style={{ display:"flex", flexDirection:"column", gap:7, marginBottom:18 }}>
            {[
              ["📍", [ev.venue_name, ev.neighborhood].filter(Boolean).join(" · ")],
              ["📅", [fmtDate(ev.event_date), ev.start_time && `${ev.start_time}${ev.end_time ? " – "+ev.end_time : ""}`].filter(Boolean).join(" · ")],
              ["🏷️", [ev.category, ev.subcategory].filter(Boolean).join(" / ")],
              ["💰", fmtPrice(ev)],
            ].filter(([,v]) => v).map(([icon,val]) => (
              <div key={icon} style={{ display:"flex", gap:10, fontFamily:T.body, fontSize:13, color:T.textMid }}>
                <span>{icon}</span><span style={{ color:"#c0d0d0" }}>{val}</span>
              </div>
            ))}
          </div>

          {ev.tags?.length > 0 && (
            <div style={{ display:"flex", gap:5, flexWrap:"wrap", marginBottom:20 }}>
              {ev.tags.map(t => <Tag key={t} label={t} />)}
            </div>
          )}

          <div style={{ display:"flex", gap:10, marginBottom:14 }}>
            <a href={ev.ticket_url || ev.source_url || "#"} target="_blank" rel="noopener noreferrer" style={{ flex:1, padding:"11px 0", background:T.amber, border:"none", borderRadius:8, fontFamily:T.font, fontSize:14, fontWeight:700, color:T.bg0, cursor:"pointer", textAlign:"center", textDecoration:"none", display:"block" }}>
              {ev.ticket_url ? "Get Tickets →" : "More Info →"}
            </a>
            <button style={{ padding:"11px 16px", background:"none", border:`1px solid ${T.border}`, borderRadius:8, fontFamily:T.font, fontSize:14, color:T.textMid, cursor:"pointer" }}>♥</button>
          </div>

          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
            <Badge source={ev.source} />
            {ev.source_url && <a href={ev.source_url} target="_blank" rel="noopener noreferrer" style={{ fontSize:10, color:T.textDim, fontFamily:T.body, textDecoration:"none" }}>View on {SOURCE_META[ev.source]?.label || ev.source} ↗</a>}
          </div>
        </div>

        {/* ── Events Like This ── */}
        {similar.length > 0 && (
          <div style={{ borderTop:`1px solid ${T.border}`, padding:"18px 28px 26px" }}>
            <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:4 }}>
              <div style={{ fontFamily:T.font, fontSize:12, fontWeight:700, color:T.text, letterSpacing:"0.06em" }}>EVENTS LIKE THIS</div>
              <button onClick={() => setShowBreakdown(v=>!v)} style={{ background:"none", border:`1px solid ${T.border}`, borderRadius:5, padding:"2px 8px", fontFamily:T.body, fontSize:9, color:T.textDim, cursor:"pointer" }}>
                {showBreakdown ? "hide" : "why?"}
              </button>
            </div>

            <div style={{ fontSize:10, color:T.textDim, fontFamily:T.body, marginBottom:12 }}>
              Ranked by Facebook audience overlap + venue + timing signals
            </div>

            {showBreakdown && pinned !== null && (() => {
              const s = SIM_INDEX[ev.id]?.[pinned] || {};
              const pinnedEv = events.find(e => e.id === pinned);
              return (
                <div style={{ background:T.bg0, border:`1px solid ${T.border}`, borderRadius:10, padding:"14px 16px", marginBottom:12 }}>
                  <div style={{ fontFamily:T.font, fontSize:10, color:T.textDim, letterSpacing:"0.06em", marginBottom:10 }}>
                    MATCH BREAKDOWN · {pinnedEv?.title?.slice(0,30)}
                  </div>
                  <ScoreBar label={"👥 User overlap (Jaccard)"}          value={s.score_user_overlap||0} color="#6366f1" />
                  <ScoreBar label="📍 Venue / neighborhood"              value={s.score_venue||0}        color="#22c55e" />
                  <ScoreBar label="🕐 Temporal pattern"                  value={s.score_temporal||0}     color="#0ea5e9" />
                  <ScoreBar label="🎭 Scene / subcategory"               value={s.score_organizer||0}    color="#a855f7" />
                  <div style={{ borderTop:`1px solid ${T.border}`, paddingTop:8, marginTop:8, display:"flex", justifyContent:"space-between" }}>
                    <span style={{ fontSize:10, color:T.textDim, fontFamily:T.body }}>Weighted composite × confidence</span>
                    <span style={{ fontSize:12, color:T.amber, fontFamily:T.font, fontWeight:700 }}>{Math.round((s.score_composite||0)*100)}%</span>
                  </div>
                  {s.overlap_user_count !== undefined && (
                    <div style={{ fontSize:9, color:T.textDim, fontFamily:T.body, marginTop:5 }}>
                      {s.overlap_user_count} shared Facebook users in sample
                    </div>
                  )}
                </div>
              );
            })()}

            <div style={{ display:"flex", gap:10, overflowX:"auto", paddingBottom:4, scrollbarWidth:"none" }}>
              {similar.map(s => (
                <div key={s.id} onMouseEnter={() => showBreakdown && setPinned(s.id)}>
                  <SimilarMini ev={s} onClick={ev2 => { setPinned(null); onNavigate(ev2); }} />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Mini Calendar ──────────────────────────────────────────────────────────
const DAY_LABELS = ["Mo","Tu","We","Th","Fr","Sa","Su"];
const MONTH_NAMES = ["January","February","March","April","May","June",
                     "July","August","September","October","November","December"];

function MiniCalendar({ range, onChange, onClose }) {
  const now = new Date(TODAY + "T00:00:00");
  const [view, setView] = useState({ y: now.getFullYear(), m: now.getMonth() });
  const [picking, setPicking] = useState(null); // "start" awaiting end click

  function isoOf(y, m, d) {
    return `${y}-${String(m+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
  }

  function daysInMonth(y, m) { return new Date(y, m+1, 0).getDate(); }
  function firstDow(y, m) { return (new Date(y, m, 1).getDay() + 6) % 7; } // Mon=0

  function handleDay(iso) {
    if (!range.start || (range.start && range.end)) {
      onChange({ start: iso, end: null });
      setPicking("end");
    } else {
      const s = range.start;
      onChange({ start: iso < s ? iso : s, end: iso < s ? s : iso });
      setPicking(null);
    }
  }

  function inRange(iso) {
    if (!range.start || !range.end) return false;
    return iso >= range.start && iso <= range.end;
  }

  const { y, m } = view;
  const days = daysInMonth(y, m);
  const offset = firstDow(y, m);
  const cells = [];
  for (let i = 0; i < offset; i++) cells.push(null);
  for (let d = 1; d <= days; d++) cells.push(d);
  while (cells.length % 7) cells.push(null);

  return (
    <div style={{ background:T.bg1, border:`1px solid ${T.border}`, borderRadius:12,
                  padding:"14px 12px", marginTop:8, userSelect:"none" }}>
      {/* Month nav */}
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:10 }}>
        <button onClick={()=>setView(v=>v.m===0?{y:v.y-1,m:11}:{y:v.y,m:v.m-1})}
          style={{ background:"none", border:"none", color:T.textMid, cursor:"pointer", fontSize:16, padding:"0 4px" }}>‹</button>
        <span style={{ fontFamily:T.font, fontSize:12, fontWeight:700, color:T.text }}>
          {MONTH_NAMES[m]} {y}
        </span>
        <button onClick={()=>setView(v=>v.m===11?{y:v.y+1,m:0}:{y:v.y,m:v.m+1})}
          style={{ background:"none", border:"none", color:T.textMid, cursor:"pointer", fontSize:16, padding:"0 4px" }}>›</button>
      </div>

      {/* Day labels */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(7,1fr)", gap:2, marginBottom:4 }}>
        {DAY_LABELS.map(d => (
          <div key={d} style={{ textAlign:"center", fontFamily:T.font, fontSize:9,
                                color:T.textDim, fontWeight:600 }}>{d}</div>
        ))}
      </div>

      {/* Day cells */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(7,1fr)", gap:2 }}>
        {cells.map((d, i) => {
          if (!d) return <div key={i} />;
          const iso = isoOf(y, m, d);
          const isStart = iso === range.start;
          const isEnd   = iso === range.end;
          const isIn    = inRange(iso);
          const isPast  = iso < TODAY;
          const isToday = iso === TODAY;
          return (
            <button key={i} onClick={()=>!isPast && handleDay(iso)}
              style={{
                padding:"5px 0", borderRadius:6, border:"none", cursor: isPast ? "default" : "pointer",
                fontFamily:T.body, fontSize:11, fontWeight: isStart||isEnd ? 700 : 400,
                background: isStart||isEnd ? T.amber : isIn ? T.amberDim : "transparent",
                color: isStart||isEnd ? T.bg0 : isPast ? T.textDim : isToday ? T.amber : T.text,
                outline: isToday && !isStart ? `1px solid ${T.amber}` : "none",
                opacity: isPast ? 0.4 : 1,
              }}>{d}</button>
          );
        })}
      </div>

      {/* Footer */}
      <div style={{ marginTop:10, display:"flex", justifyContent:"space-between", alignItems:"center" }}>
        <span style={{ fontFamily:T.body, fontSize:10, color:T.textMid }}>
          {range.start && !range.end ? "Tap end date" :
           range.start && range.end && range.start===range.end ? range.start :
           range.start && range.end ? `${range.start} → ${range.end}` : "Tap a date"}
        </span>
        <div style={{ display:"flex", gap:6 }}>
          {range.start && (
            <button onClick={()=>{ onChange({start:null,end:null}); setPicking(null); }}
              style={{ background:"none", border:"none", color:T.textDim, fontFamily:T.body,
                       fontSize:10, cursor:"pointer" }}>Clear</button>
          )}
          <button onClick={onClose}
            style={{ background:T.bg2, border:`1px solid ${T.border}`, color:T.textMid,
                     fontFamily:T.font, fontSize:10, fontWeight:600, padding:"3px 10px",
                     borderRadius:6, cursor:"pointer" }}>Done</button>
        </div>
      </div>
    </div>
  );
}

// ── Date nav strip ─────────────────────────────────────────────────────────
const DATE_FILTERS = [
  { id:"today",     label:"Today"     },
  { id:"tomorrow",  label:"Tomorrow"  },
  { id:"weekend",   label:"Weekend"   },
  { id:"next-week", label:"Next Week" },
  { id:"all",       label:"All"       },
];

const CATEGORIES = [
  { id:"all",      label:"All",      emoji:"✦" },
  { id:"music",    label:"Music",    emoji:"🎵" },
  { id:"dj-set",   label:"DJ Sets",  emoji:"🎧" },
  { id:"cultural", label:"Cultural", emoji:"✨" },
  { id:"market",   label:"Markets",  emoji:"🛍️" },
];

// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [events,    setEvents]    = useState(DB.events);
  const [loading,   setLoading]   = useState(true);
  const [dateFil,   setDateFil]   = useState("weekend");
  const [dateRange, setDateRange] = useState({ start: null, end: null });
  const [calOpen,   setCalOpen]   = useState(false);
  const [catFil,    setCatFil]    = useState("all");
  const [priceFil,  setPriceFil]  = useState("all");
  const [search,    setSearch]    = useState("");
  const [selected,  setSelected]  = useState(null);
  const [history,   setHistory]   = useState([]);

  useEffect(() => {
    fetch("/api/events")
      .then(r => r.json())
      .then(d => { setEvents(d.events); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  function openEvent(ev)  { setSelected(ev); setHistory([]); }
  function navSimilar(ev) { setHistory(h => [...h, selected]); setSelected(ev); }
  function closeModal()   { setSelected(null); setHistory([]); }

  const filtered = useMemo(() => {
    return events.filter(ev => {
      if (!matchDate(ev, dateFil, dateRange)) return false;
      if (catFil === "dj-set" && ev.subcategory !== "dj-set") return false;
      if (catFil !== "all" && catFil !== "dj-set" && ev.category !== catFil) return false;
      if (priceFil === "free" && ev.price_min !== 0) return false;
      if (priceFil === "paid" && ev.price_min === 0) return false;
      if (search) {
        const q = search.toLowerCase();
        return ev.title.toLowerCase().includes(q) ||
          (ev.venue_name||"").toLowerCase().includes(q) ||
          (ev.neighborhood||"").toLowerCase().includes(q) ||
          (ev.tags||[]).some(t => t.toLowerCase().includes(q));
      }
      return true;
    }).sort((a,b) => {
      if (a.event_date !== b.event_date) return a.event_date < b.event_date ? -1 : 1;
      return (a.start_time||"") < (b.start_time||"") ? -1 : 1;
    });
  }, [events, dateFil, dateRange, catFil, priceFil, search]);

  // Group by date
  const grouped = useMemo(() => {
    const g = {};
    for (const ev of filtered) {
      if (!g[ev.event_date]) g[ev.event_date] = [];
      g[ev.event_date].push(ev);
    }
    return g;
  }, [filtered]);

  const todayCount = events.filter(e => e.event_date === TODAY).length;

  return (
    <div style={{ minHeight:"100vh", background:T.bg0, color:T.text, fontFamily:T.body }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');
        @keyframes pulse { 0%{box-shadow:0 0 0 0 rgba(245,166,35,0.7)} 70%{box-shadow:0 0 0 7px rgba(245,166,35,0)} 100%{box-shadow:0 0 0 0 rgba(245,166,35,0)} }
        * { box-sizing:border-box; margin:0; padding:0; }
        ::-webkit-scrollbar{width:3px;height:3px}
        ::-webkit-scrollbar-track{background:transparent}
        ::-webkit-scrollbar-thumb{background:#2a3a3a;border-radius:4px}
        a{color:inherit}
      `}</style>

      {/* ── Header ── */}
      <header style={{ position:"sticky", top:0, background:"rgba(8,14,14,0.96)", backdropFilter:"blur(14px)", zIndex:100, borderBottom:`1px solid ${T.border}` }}>
        <div style={{ maxWidth:1100, margin:"0 auto", padding:"18px 24px 0" }}>

          {/* Brand row */}
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:16 }}>
            <div>
              <div style={{ fontFamily:T.font, fontSize:22, fontWeight:800, letterSpacing:"-0.02em", lineHeight:1 }}>
                my<span style={{ color:T.amber }}>tlv</span><span style={{ color:T.textDim, fontSize:17 }}>.ai</span>
              </div>
              <div style={{ fontSize:10, color:T.textDim, fontFamily:T.body, marginTop:3 }}>
                Tel Aviv · <span style={{ color:T.amber }}>{todayCount}</span> events today · {events.length} total
              </div>
            </div>

            {/* Search */}
            <div style={{ display:"flex", alignItems:"center", gap:8, background:T.bg1, border:`1px solid ${T.border}`, borderRadius:8, padding:"7px 12px", width:220 }}>
              <span style={{ color:T.textDim, fontSize:13 }}>⌕</span>
              <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search events, venues…"
                style={{ background:"none", border:"none", outline:"none", color:T.text, fontFamily:T.body, fontSize:12, width:"100%" }} />
              {search && <button onClick={()=>setSearch("")} style={{ background:"none", border:"none", color:T.textDim, cursor:"pointer", fontSize:12, padding:0 }}>✕</button>}
            </div>
          </div>

          {/* Date strip + price */}
          <div style={{ display:"flex", gap:5, alignItems:"center", overflowX:"auto", paddingBottom:12, scrollbarWidth:"none" }}>
            {DATE_FILTERS.map(df => (
              <button key={df.id} onClick={()=>{ setDateFil(df.id); setDateRange({start:null,end:null}); setCalOpen(false); }} style={{
                padding:"5px 13px", borderRadius:6, border:"none", whiteSpace:"nowrap",
                background: !dateRange.start && dateFil===df.id ? T.amber : T.bg2,
                color: !dateRange.start && dateFil===df.id ? T.bg0 : T.textMid,
                fontFamily:T.font, fontSize:11, fontWeight: !dateRange.start && dateFil===df.id ? 700 : 500, cursor:"pointer",
              }}>{df.label}</button>
            ))}
            {/* Calendar toggle */}
            <button onClick={()=>setCalOpen(o=>!o)} style={{
              padding:"5px 10px", borderRadius:6, border:"none", whiteSpace:"nowrap", flexShrink:0,
              background: dateRange.start ? T.amber : calOpen ? T.bg2 : "transparent",
              color: dateRange.start ? T.bg0 : T.textMid,
              fontFamily:T.font, fontSize:11, fontWeight: dateRange.start ? 700 : 500, cursor:"pointer",
            }}>
              {dateRange.start
                ? (dateRange.end && dateRange.end !== dateRange.start
                    ? `${dateRange.start.slice(5)} – ${dateRange.end.slice(5)}`
                    : dateRange.start.slice(5))
                : "📅"}
            </button>
            <div style={{ marginLeft:"auto", display:"flex", gap:4 }}>
              {["all","free","paid"].map(p => (
                <button key={p} onClick={()=>setPriceFil(p)} style={{
                  padding:"5px 10px", borderRadius:6, border:"none",
                  background: priceFil===p ? T.teal : "transparent",
                  color: priceFil===p ? T.tealBright : T.textDim,
                  fontFamily:T.font, fontSize:10, fontWeight:600, cursor:"pointer", whiteSpace:"nowrap",
                }}>
                  {p==="all" ? "All prices" : p.charAt(0).toUpperCase()+p.slice(1)}
                </button>
              ))}
            </div>
          </div>
          {calOpen && (
            <MiniCalendar
              range={dateRange}
              onChange={r=>{ setDateRange(r); if(r.start) setDateFil("all"); }}
              onClose={()=>setCalOpen(false)}
            />
          )}

          {/* Category pills */}
          <div style={{ display:"flex", gap:6, overflowX:"auto", paddingBottom:14, scrollbarWidth:"none" }}>
            {CATEGORIES.map(c => (
              <button key={c.id} onClick={()=>setCatFil(c.id)} style={{
                display:"flex", alignItems:"center", gap:5, padding:"7px 14px", borderRadius:100, border:"none", whiteSpace:"nowrap",
                background: catFil===c.id ? T.amberDim : "transparent",
                border: catFil===c.id ? `1.5px solid ${T.amber}` : `1.5px solid ${T.border}`,
                color: catFil===c.id ? T.amber : T.textMid,
                fontFamily:T.font, fontSize:12, fontWeight: catFil===c.id ? 700 : 500, cursor:"pointer",
              }}>
                <span>{c.emoji}</span>{c.label}
              </button>
            ))}

            {/* Source legend */}
            <div style={{ marginLeft:"auto", display:"flex", gap:6, alignItems:"center", flexShrink:0 }}>
              {Object.entries(SOURCE_META).slice(0,4).map(([k,v]) => (
                <span key={k} style={{ fontSize:9, fontFamily:T.font, fontWeight:700, color:v.color, background:v.color+"15", padding:"3px 7px", borderRadius:4 }}>{v.label}</span>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* ── Main content ── */}
      <main style={{ maxWidth:1100, margin:"0 auto", padding:"24px 24px 60px" }}>

        {filtered.length === 0 ? (
          <div style={{ textAlign:"center", padding:"80px 0", color:T.textDim, fontFamily:T.font, fontSize:15 }}>
            <div style={{ fontSize:36, marginBottom:12 }}>🌙</div>
            Nothing found — try "Weekend" or clear the filter
          </div>
        ) : (
          Object.entries(grouped).map(([dateKey, evs]) => (
            <div key={dateKey} style={{ marginBottom:32 }}>
              {/* Date section header */}
              <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:14 }}>
                <div style={{ fontFamily:T.font, fontSize:13, fontWeight:700, color:T.amber, letterSpacing:"0.06em" }}>
                  {fmtDate(dateKey).toUpperCase()}
                </div>
                <div style={{ flex:1, height:1, background:T.border }} />
                <div style={{ fontFamily:T.body, fontSize:10, color:T.textDim }}>{evs.length} event{evs.length!==1?"s":""}</div>
              </div>

              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(270px,1fr))", gap:12 }}>
                {evs.map(ev => <EventCard key={ev.id} ev={ev} onClick={openEvent} />)}
              </div>
            </div>
          ))
        )}

        {/* Data sources footer */}
        <div style={{ marginTop:48, borderTop:`1px solid ${T.border}`, paddingTop:24 }}>
          <div style={{ fontFamily:T.font, fontSize:10, color:T.textDim, letterSpacing:"0.08em", marginBottom:12 }}>DATA SOURCES</div>
          <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
            {[
              ["Secret Tel Aviv",    "🟢 Tribe REST API",    "#e879f9"],
              ["Entrio",             "🟢 HTML scraper",      "#6366f1"],
              ["Bandsintown",        "🟢 REST API",          "#22c55e"],
              ["TLV Municipality",   "🟡 HTML scraper",      "#a855f7"],
              ["Facebook Events",    "🔴 Planned",           "#3b82f6"],
              ["Ticketmaster IL",    "🟡 REST API",          "#0ea5e9"],
            ].map(([name, status, color]) => (
              <div key={name} style={{ background:T.bg1, border:`1px solid ${T.border}`, borderRadius:8, padding:"9px 13px" }}>
                <div style={{ fontFamily:T.font, fontSize:11, color:T.text, fontWeight:600, marginBottom:2 }}>{name}</div>
                <div style={{ fontFamily:T.body, fontSize:9, color:T.textDim }}>{status}</div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* ── Modal ── */}
      {selected && <Modal ev={selected} events={events} onClose={closeModal} onNavigate={navSimilar} />}
    </div>
  );
}
