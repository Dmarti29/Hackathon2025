from flask import Flask, request, jsonify
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)

# Ultra-expanded list of productive domains
PRODUCTIVE_DOMAINS = [
    # Educational
    'wikipedia.org', 'scholar.google.com', 'coursera.org', 'edx.org', 
    'khanacademy.org', 'jstor.org', 'researchgate.net', 'arxiv.org',
    'gutenberg.org', 'mitopencourseware.org', 'ocw.mit.edu', 'britannica.com',
    'quizlet.com', 'academicjournals.org', 'sciencedirect.com', 'nature.com',
    'ieee.org', 'academia.edu', 'ebsco.com', 'projecteuclid.org',
    'oup.com', 'tandfonline.com', 'wiley.com', 'springer.com', 'sagepub.com',
    'ebooks.com', 'questia.com', 'proquest.com', 'worldcat.org',
    'ncbi.nlm.nih.gov', 'pubmed.gov', 'eric.ed.gov', 'merlot.org',
    'library.edu', 'doaj.org', 'repec.org', 'ssrn.com', 'nber.org',
    'oercommons.org', 'sparknotes.com', 'cliffsnotes.com', 'schmoop.com',
    'mathworld.wolfram.com', 'wolframalpha.com', 'openculture.com',
    'mendeley.com', 'citeseerx.ist.psu.edu', 'crossref.org', 'zotero.org',
    'refworks.com', 'endnote.com', 'grammarly.com', 'turnitin.com',
    'scihub.org', 'sci-hub.se', 'sci-hub.st', 'libgen.is', 'libgen.rs',
    'booksc.org', 'pdfdrive.com', 'semanticscholar.org', 'readcube.com',
    'deepdyve.com', 'scienceopen.com', 'erudit.org', 'cairn.info',
    'persee.fr', 'dialnet.unirioja.es', 'redalyc.org', 'scielo.org',
    'dblp.org', 'zbmath.org', 'ams.org/mathscinet', 'mathscinet.ams.org',
    'informs.org', 'ajol.info', 'sabinet.co.za', 'cnki.net', 'wanfangdata.com',
    'cqvip.com', 'jstage.jst.go.jp', 'koreascience.or.kr', 'ndl.go.jp',
    'nii.ac.jp', 'webofknowledge.com', 'scopus.com', 'clarivate.com',
    'dimensions.ai', 'lens.org', 'base-search.net', 'core.ac.uk',
    'openaire.eu', 'zenodo.org', 'figshare.com', 'dryad.org',
    'datadryad.org', 'dataverse.org', 'opendata.cern.ch', 'data.gov',
    'gislounge.com', 'esri.com', 'arcgis.com', 'qgis.org',
    
    # Learning platforms
    'udemy.com', 'udacity.com', 'pluralsight.com', 'lynda.com', 'skillshare.com',
    'codecademy.com', 'freecodecamp.org', 'brilliant.org', 'datacamp.com',
    'futurelearn.com', 'open2study.com', 'canvas.net', 'canvas.edu', 'blackboard.com',
    'moodle.org', 'schoology.com', 'duolingo.com', 'memrise.com', 'busuu.com',
    'rosettastone.com', 'edx.org', 'open.edu', 'alison.com', 'openlearning.com',
    'ted.com', 'edutopia.org', 'teachable.com', 'brainly.com', 'masterclass.com',
    'thegreatcourses.com', 'edraak.org', 'rwaq.org', 'swayam.gov.in', 'nptel.ac.in',
    'classcentral.com', 'edureka.co', 'simplilearn.com', 'sololearn.com',
    'learndash.com', 'thinkific.com', 'podia.com', 'kajabi.com', 'ruzuku.com',
    'learningcart.com', 'educadium.com', 'talentlms.com', 'absorblms.com',
    'docebo.com', 'litmos.com', 'accessibyte.com', 'edmentum.com', 'edgenuity.com',
    'ixl.com', 'mathway.com', 'symbolab.com', 'desmos.com', 'geogebra.org',
    'studystack.com', 'goconqr.com', 'cerego.com', 'mondly.com', 'lingvist.com',
    'lingq.com', 'tandem.net', 'italki.com', 'fluentu.com', 'membean.com',
    'vocabulary.com', 'quill.org', 'readworks.org', 'newsela.com', 'getepic.com',
    'readtheory.org', 'commonlit.org', 'activelylearn.com', 'readwritethink.org',
    'noredink.com', 'grammarcheck.net', 'writingexplained.org', 'hemingwayapp.com',
    'chegg.com', 'bartleby.com', 'slader.com', 'studyblue.com', 'cram.com',
    'tinycards.duolingo.com', 'ankiweb.net', 'memcode.com', 'supermemo.com',
    
    # Programming and technical
    'github.com', 'stackoverflow.com', 'gitlab.com', 'bitbucket.org', 'replit.com',
    'codeacademy.com', 'leetcode.com', 'hackerrank.com', 'codewars.com',
    'w3schools.com', 'mozilla.org', 'developer.mozilla.org', 'docs.python.org',
    'cplusplus.com', 'ruby-doc.org', 'php.net', 'javadocs.org', 'kotlinlang.org',
    'reactjs.org', 'vuejs.org', 'angular.io', 'tensorflow.org', 'pytorch.org',
    'kaggle.com', 'medium.com/programming', 'dev.to', 'codesandbox.io',
    'docker.com', 'kubernetes.io', 'aws.amazon.com/documentation', 'cloud.google.com/docs',
    'confluence.atlassian.com', 'devdocs.io', 'geeksforgeeks.org', 'tutorialspoint.com',
    'hackr.io', 'educative.io', 'scotch.io', 'sitepoint.com', 'css-tricks.com',
    'smashingmagazine.com', 'alistapart.com', 'html5rocks.com', 'webplatform.org',
    'digitalocean.com/community/tutorials', 'baeldung.com', 'javatpoint.com',
    'learnpython.org', 'numpy.org', 'scipy.org', 'pandas.pydata.org',
    'scikit-learn.org', 'matplotlib.org', 'seaborn.pydata.org', 'statsmodels.org',
    'julialang.org', 'rstudio.com', 'r-project.org', 'r-bloggers.com',
    'thecodingtrain.com', 'eloquentjavascript.net', 'javascript.info',
    'htmldog.com', 'learn-c.org', 'learncpp.com', 'learnjavaonline.org',
    'overapi.com', 'devhints.io', 'explainshell.com', 'gobyexample.com',
    'rust-lang.org', 'rustbyexample.com', 'go.dev', 'godoc.org', 'elixir-lang.org',
    'erlang.org', 'haskell.org', 'swift.org', 'kotlinlang.org', 'scala-lang.org',
    'clojure.org', 'ocaml.org', 'elm-lang.org', 'typescriptlang.org',
    'dartlang.org', 'flutter.dev', 'reactnative.dev', 'android.com/develop',
    'developer.apple.com', 'docs.microsoft.com', 'learn.microsoft.com',
    'channel9.msdn.com', 'docs.oracle.com', 'ibm.com/developerworks',
    'developer.ibm.com', 'developer.salesforce.com', 'developer.mozilla.org',
    'developer.chrome.com', 'web.dev', 'developers.google.com',
    
    # Scientific and research
    'arxiv.org', 'biorxiv.org', 'medrxiv.org', 'chemrxiv.org', 'osf.io',
    'frontiersin.org', 'plos.org', 'sciencemag.org', 'pnas.org', 'acs.org',
    'cell.com', 'nejm.org', 'aip.org', 'ams.org', 'aps.org', 'pubs.rsc.org',
    'science.gov', 'scienceopen.com', 'scicrunch.org', 'orcid.org',
    'clinicaltrials.gov', 'who.int/research', 'epa.gov/research', 'nasa.gov/research',
    'nsf.gov', 'nih.gov', 'cdc.gov', 'noaa.gov', 'usgs.gov', 'niaid.nih.gov',
    'genome.gov', 'energy.gov/science', 'ornl.gov', 'lbl.gov', 'anl.gov',
    'bnl.gov', 'lanl.gov', 'fnal.gov', 'slac.stanford.edu', 'llnl.gov',
    'pnnl.gov', 'nrel.gov', 'nist.gov', 'jpl.nasa.gov', 'scripps.edu',
    'salk.edu', 'whitehead.mit.edu', 'broadinstitute.org', 'hudsonalpha.org',
    'embl.org', 'ebi.ac.uk', 'sanger.ac.uk', 'wellcome.ac.uk', 'max-planck.de',
    'fraunhofer.de', 'helmholtz.de', 'cnrs.fr', 'inserm.fr', 'csic.es',
    'cnr.it', 'csiro.au', 'riken.jp', 'cas.cn', 'iitd.ac.in', 'tifr.res.in',
    
    # News and knowledge
    'economist.com', 'scientificamerican.com', 'smithsonianmag.com', 'newscientist.com',
    'nationalgeographic.com', 'popsci.com', 'arstechnica.com', 'wired.com/category/science',
    'phys.org', 'sciencedaily.com', 'livescience.com', 'spectrum.ieee.org',
    'quantamagazine.org', 'nautil.us', 'hhmi.org', 'wellcome.org',
    'sciencefriday.com', 'sciencenews.org', 'insidescience.org', 'science.org',
    'technologyreview.com', 'nature.com/news', 'sciencebasedmedicine.org',
    'physicsworld.com', 'chemistryworld.com', 'earthsky.org', 'space.com',
    'universetoday.com', 'skyandtelescope.org', 'astronomy.com',
    'spaceflightnow.com', 'nasaspaceflight.com', 'thespacereview.com',
    'spaceflightinsider.com', 'arstechnica.com/science', 'futurity.org',
    'scienceblogs.com', 'sciencemuseum.org.uk', 'amnh.org', 'fieldmuseum.org',
    'nhm.ac.uk', 'calacademy.org', 'si.edu', 'nasm.si.edu', 'nhmla.org',
    'rbg.vic.gov.au', 'rbgkew.org.uk', 'botanicgardens.org', 'nybg.org',
    'mnh.si.edu', 'peabody.yale.edu', 'cmnh.org', 'hmnh.harvard.edu',
    
    # Reference
    'dictionary.com', 'merriam-webster.com', 'thesaurus.com', 'etymonline.com',
    'encyclopedia.com', 'stanford.edu', 'harvard.edu', 'yale.edu', 'mit.edu',
    'berkeley.edu', 'caltech.edu', 'ox.ac.uk', 'cam.ac.uk', 'princeton.edu',
    'columbia.edu', 'uchicago.edu', 'cornell.edu', 'upenn.edu', 'duke.edu',
    'jhu.edu', 'nyu.edu', 'northwestern.edu', 'cmu.edu', 'rice.edu',
    'ucla.edu', 'ucsb.edu', 'ucsd.edu', 'ucdavis.edu', 'umich.edu',
    'wisc.edu', 'illinois.edu', 'psu.edu', 'gatech.edu', 'purdue.edu',
    'utexas.edu', 'tamu.edu', 'uw.edu', 'washington.edu', 'ucsf.edu',
    'arizona.edu', 'asu.edu', 'colorado.edu', 'umn.edu', 'osu.edu',
    'ufl.edu', 'ncsu.edu', 'uci.edu', 'rutgers.edu', 'uiowa.edu',
    'indiana.edu', 'uwaterloo.ca', 'utoronto.ca', 'mcgill.ca',
    'ubc.ca', 'usyd.edu.au', 'anu.edu.au', 'unimelb.edu.au',
    'unsw.edu.au', 'kcl.ac.uk', 'ucl.ac.uk', 'imperial.ac.uk',
    'ed.ac.uk', 'manchester.ac.uk', 'bristol.ac.uk', 'warwick.ac.uk',
    'lse.ac.uk', 'tcd.ie', 'ethz.ch', 'epfl.ch', 'uni-heidelberg.de',
    'hu-berlin.de', 'uni-muenchen.de', 'tum.de', 'sorbonne-universite.fr',
    'u-tokyo.ac.jp', 'kyoto-u.ac.jp', 'tsinghua.edu.cn', 'pku.edu.cn',
    'nus.edu.sg', 'ntu.edu.sg', 'unam.mx', 'usp.br', 'uct.ac.za'
]

# Ultra-expanded list of unproductive domains
UNPRODUCTIVE_DOMAINS = [
    # Social media
    'facebook.com', 'twitter.com', 'instagram.com', 'snapchat.com', 'tiktok.com',
    'reddit.com', 'tumblr.com', 'pinterest.com', 'linkedin.com/feed', 'myspace.com',
    'vk.com', 'weibo.com', 'flickr.com', 'imgur.com', 'discord.com', 'telegram.org',
    'whatsapp.com', 'messenger.com', 'viber.com', 'line.me', 'kik.com',
    'wechat.com', 'kakaotalk.com', 'reddit.com/r/funny', 'reddit.com/r/pics',
    'reddit.com/r/gaming', 'reddit.com/r/aww', 'reddit.com/r/videos',
    'reddit.com/r/gifs', 'reddit.com/r/memes', 'reddit.com/r/askreddit',
    'reddit.com/r/jokes', 'reddit.com/r/tifu', 'reddit.com/r/showerthoughts',
    'reddit.com/r/worldnews', 'reddit.com/r/news', 'reddit.com/r/todayilearned',
    'reddit.com/r/explainlikeimfive', 'reddit.com/r/science', 'reddit.com/r/iama',
    'reddit.com/r/dataisbeautiful', 'reddit.com/r/upliftingnews', 'reddit.com/r/books',
    'reddit.com/r/movies', 'reddit.com/r/television', 'reddit.com/r/music',
    'qzone.qq.com', 'tieba.baidu.com', 'douban.com', 'renren.com',
    'ok.ru', 'tagged.com', 'meetme.com', 'meetup.com', 'nextdoor.com',
    'threads.net', 'bluesky.app', 'mastodon.social', 'truthsocial.com',
    'gab.com', 'minds.com', 'parler.com', 'gettr.com', 'clubhouse.com',
    'houseparty.com', 'caffeine.tv', 'younow.com', 'periscope.tv',
    'mixer.com', 'dlive.tv', 'trovo.live', 'bigo.tv', 'likee.com',
    'kuaishou.com', 'zynn.app', 'lomotif.com', 'funimate.com', 'triller.co',
    'musical.ly', 'vsco.co', 'meipai.com', 'yizhibo.com', 'xiaohongshu.com',
    'douyin.com', 'kwai.com', 'momo.com', 'tantan.com', 'bumble.com',
    'match.com', 'tinder.com', 'badoo.com', 'okcupid.com', 'pof.com',
    'zoosk.com', 'eharmony.com', 'hinge.co', 'grindr.com', 'scruff.com',
    'taimi.com', 'her.app', 'coffee.com', 'meetmindful.com', 'feeld.co',
    'pixiv.net', 'deviantart.com', 'artstation.com', 'behance.net',
    'dribbble.com', 'ello.co', 'pillowfort.social', 'livejournal.com',
    'dreamwidth.org', 'blogspot.com', 'wordpress.com', 'medium.com',
    'substack.com', 'ghost.org', 'wattpad.com', 'goodreads.com',
    'librarything.com', 'anobii.com', 'bookcrossing.com', 'bookstr.com',
    
    # Streaming services
    'youtube.com/shorts', 'youtube.com/reels', 'netflix.com', 'hulu.com', 'disneyplus.com',
    'primevideo.com', 'hbomax.com', 'peacocktv.com', 'paramountplus.com', 'appletv.com',
    'espn.com', 'twitch.tv', 'vimeo.com/browse', 'dailymotion.com', 'crunchyroll.com',
    'funimation.com', 'youtube.com/gaming', 'youtube.com/trends', 'youtube.com/feed/trending',
    'youtube.com/explore', 'youtube.com/feed/explore', 'youtube.com/feed/subscriptions',
    'youtube.com/feed/history', 'youtube.com/feed/library', 'youtube.com/feed/purchases',
    'youtube.com/feed/recommended', 'youtube.com/feed/trending', 'youtube.com/feed/music',
    'youtube.com/feed/news', 'youtube.com/feed/sports', 'youtube.com/feed/gaming',
    'youtube.com/feed/movies', 'youtube.com/feed/fashion', 'youtube.com/feed/beauty',
    'youtube.com/feed/comedy', 'youtube.com/feed/entertainment', 'youtube.com/feed/howto',
    'youtube.com/feed/science', 'youtube.com/feed/tech', 'youtube.com/feed/popular',
    'youtube.com/gaming', 'youtube.com/movies', 'youtube.com/premium', 'vudu.com',
    'hbo.com', 'showtime.com', 'starz.com', 'cbs.com', 'nbc.com', 'abc.com',
    'fox.com', 'cwtv.com', 'pbs.org', 'fxnetworks.com', 'amc.com', 'bravotv.com',
    'history.com', 'nationalgeographic.com/tv', 'discovery.com', 'animalplanet.com',
    'tlc.com', 'foodnetwork.com', 'hgtv.com', 'travel.com', 'tnt.com', 'tbs.com',
    'comedycentral.com', 'mtv.com', 'vh1.com', 'bet.com', 'nick.com', 'disneychannel.com',
    'cartoonnetwork.com', 'adultswim.com', 'crackle.com', 'tubitv.com', 'pluto.tv',
    'imdb.com/tv', 'roosterteeth.com', 'dramafever.com', 'viki.com', 'viewster.com',
    'contv.com', 'acorn.tv', 'britbox.com', 'shudder.com', 'mubi.com', 'curiositystream.com',
    'fandor.com', 'filmstruck.com', 'criterion.com', 'snagfilms.com', 'popcornflix.com',
    'pureflix.com', 'docurama.com', 'realeyz.com', 'fandangonow.com', 'redbox.com',
    'skyshowtime.com', 'now.com', 'stan.com.au', 'binge.com', 'crave.ca', 'zee5.com',
    'hotstar.com', 'sonyliv.com', 'altbalaji.com', 'erosnow.com', 'hungama.com',
    'voot.com', 'mxplayer.in', 'jiotv.com', 'iqiyi.com', 'youku.com', 'tudou.com',
    'qqlive.com', 'pptv.com', 'bilibili.com', 'niconico.jp', 'gyao.yahoo.co.jp',
    'abematv.com', 'viu.com', 'iflix.com', 'hooq.tv', 'wavve.com', 'tving.com',
    'naver.com/tv', 'wetv.vip', 'vidio.com', 'iflix.com', 'viu.com', 'starhub.com/tv',
    
    # Gaming
    'steampowered.com', 'epicgames.com', 'origin.com', 'battle.net', 'ubisoft.com',
    'playstation.com', 'xbox.com', 'nintendo.com', 'ea.com', 'blizzard.com',
    'roblox.com', 'minecraft.net', 'kongregate.com', 'miniclip.com', 'addictinggames.com',
    'pogo.com', 'games.com', 'crazygames.com', 'y8.com', 'friv.com', 'gamesgames.com',
    'agame.com', 'games.yahoo.com', 'gaiaonline.com', 'ign.com', 'gamespot.com',
    'polygon.com', 'kotaku.com', 'rockstargames.com', 'playstation.com/store',
    'playstation.com/ps5', 'playstation.com/ps4', 'playstation.com/psvr',
    'playstation.com/psn', 'playstation.com/ps-plus', 'playstation.com/ps-now',
    'xbox.com/games', 'xbox.com/xbox-one', 'xbox.com/xbox-series-x',
    'xbox.com/xbox-series-s', 'xbox.com/xbox-game-pass', 'xbox.com/xbox-live',
    'nintendo.com/switch', 'nintendo.com/games', 'nintendo.com/3ds',
    'nintendo.com/wiiu', 'nintendo.com/eshop', 'nintendo.com/switch-online',
    'ea.com/games', 'ea.com/ea-play', 'ea.com/sports', 'ea.com/originals',
    'ubisoft.com/games', 'ubisoft.com/uplay', 'ubisoft.com/ubisoft-plus',
    'bethesda.net', 'bethesda.net/games', 'bethesda.net/launcher',
    'activision.com', 'callofduty.com', 'warzone.com', 'crashbandicoot.com',
    'spyrothedragon.com', 'tonyhawkgame.com', 'squareenix.com', 'finalfantasy.com',
    'dragonquest.com', 'kingdomhearts.com', 'tombraider.com', 'justcause.com',
    'capcom.com', 'residentevil.com', 'monsterhunter.com', 'streetfighter.com',
    'devilmaycry.com', 'bandainamco.com', 'tekken.com', 'pacman.com',
    'darksouls.com', 'eldenring.com', 'sega.com', 'sonic.com', 'yakuza.sega.com',
    'persona.atlus.com', 'koei.co.jp', 'dynasty-warriors.com', 'samuraiwarriors.com',
    'ninjagaiden.com', 'konami.com', 'metalgear.com', 'silenthill.com',
    'castlevania.com', 'yugioh.com', 'thqnordic.com', 'deepsilver.com',
    'focus-home.com', 'devolverdigital.com', 'annapurna.com', '2k.com',
    'rockstargames.com', 'gtav.com', 'reddeadredemption.com', 'bioshock.com',
    'borderlands.com', 'mafia.com', 'nba2k.com', 'wwe2k.com', 'civilization.com',
    'xcom.com', 'cdprojektred.com', 'cyberpunk.net', 'witcher.com', 'gog.com',
    'obsidian.net', 'inxile.com', 'playground-games.com', 'bethesda.net',
    'zenimax.com', 'mojang.com', 'bungie.net', 'guerrilla-games.com',
    'insomniacgames.com', 'naughtydog.com', 'suckerpunch.com', 'sucker-punch.com',
    'santa-monica.com', 'santamonicagames.com', 'bend.com', 'bendstudio.com',
    
    # Entertainment
    'buzzfeed.com', 'tmz.com', 'eonline.com', 'hollywoodreporter.com', 'variety.com',
    'popsugar.com', 'gossip.com', 'peoplemagazine.com', 'etonline.com', 'perezhilton.com',
    'cosmopolitan.com', 'complex.com', 'theonion.com', 'cracked.com', 'collegehumor.com',
    'funnyordie.com', '9gag.com', 'boredpanda.com', 'thechive.com', 'ranker.com',
    'worldstarhiphop.com', 'knowyourmeme.com', 'memecenter.com', 'memedroid.com',
    'gifbin.com', 'giphy.com', 'tenor.com', 'memegenerator.net',
    'people.com', 'usmagazine.com', 'instyle.com', 'elle.com', 'harpersbazaar.com',
    'glamour.com', 'vogue.com', 'marieclaire.com', 'gq.com', 'esquire.com',
    'menshealth.com', 'womenshealth.com', 'shape.com', 'seventeen.com',
    'teenvogue.com', 'allure.com', 'wmagazine.com', 'vanityfair.com',
    'rollingstone.com', 'billboard.com', 'spin.com', 'pitchfork.com',
    'stereogum.com', 'consequenceofsound.net', 'nme.com', 'metalinjection.net',
    'blabbermouth.net', 'loudwire.com', 'ultimate-guitar.com', 'guitarworld.com',
    'mixmag.net', 'djmag.com', 'xlr8r.com', 'factmag.com', 'resident-advisor.net',
    'ew.com', 'deadline.com', 'screenrant.com', 'cinemablend.com', 'indiewire.com',
    'collider.com', 'slashfilm.com', 'joblo.com', 'firstshowing.net',
    'comingsoon.net', 'movieweb.com', 'comicbookmovie.com', 'superherohype.com',
    'comicbook.com', 'cbr.com', 'bleedingcool.com', 'newsarama.com',
    'gamesradar.com', 'pcgamer.com', 'gameinformer.com', 'gamasutra.com',
    'eurogamer.net', 'vg247.com', 'destructoid.com', 'gametrailers.com',
    'gamerevolution.com', 'gamefaqs.com', 'giantbomb.com', 'gamespot.com',
    'n4g', 'giantbomb.com', 'gamespot.com',
    'n4g.com', 'pushsquare.com', 'nintendolife.com', 'gamereactor.eu',
    'dualshockers.com', 'playstationlifestyle.net', 'xboxachievements.com',
    'trueachievements.com', 'psnprofiles.com', 'retronauts.com',
    
    # Shopping/Browsing
    'amazon.com/browse', 'ebay.com/browse', 'walmart.com/browse', 'target.com/browse',
    'wish.com', 'aliexpress.com', 'etsy.com/browse', 'shein.com', 'fashionnova.com',
    'zara.com', 'hm.com', 'forever21.com', 'asos.com', 'nordstrom.com', 'macys.com',
    'bestbuy.com/browse', 'newegg.com/browse', 'wayfair.com', 'ikea.com/browse',
    'homedepot.com/browse', 'lowes.com/browse', 'sephora.com', 'ulta.com',
    'shopify.com', 'wix.com/shopping', 'overstock.com', 'jcpenney.com',
    'kohls.com', 'costco.com', 'samsclub.com', 'bjs.com', 'tjmaxx.com',
    'marshalls.com', 'homegoods.com', 'pier1.com', 'crateandbarrel.com',
    'cb2.com', 'potterybarn.com', 'westelm.com', 'anthropologie.com',
    'urbanoutfitters.com', 'freepeople.com', 'loft.com', 'anntaylor.com',
    'gap.com', 'oldnavy.com', 'abercrombie.com', 'ae.com', 'hollisterco.com',
    'uniqlo.com', 'lululemon.com', 'athleta.com', 'nike.com', 'adidas.com',
    'underarmour.com', 'puma.com', 'reebok.com', 'newbalance.com', 'converse.com',
    'vans.com', 'timberland.com', 'drmartens.com', 'crocs.com', 'ugg.com',
    'skechers.com', 'clarks.com', 'ninewest.com', 'stevemadden.com',
    'stuartweitzman.com', 'jimmychoo.com', 'manoloblahnik.com', 'louboutin.com',
    'gucci.com', 'louisvuitton.com', 'prada.com', 'chanel.com', 'dior.com',
    'burberry.com', 'versace.com', 'armani.com', 'calvinklein.com', 'tommyhilfiger.com',
    'ralphlauren.com', 'michaelkors.com', 'coach.com', 'katespade.com',
    'toryburch.com', 'marcjacobs.com', 'valentino.com', 'balenciaga.com',
    'fendi.com', 'hermes.com', 'tiffany.com', 'pandora.net', 'swarovski.com',
    'cartier.com', 'bulgari.com', 'rolex.com', 'omega.com', 'tagheuer.com',
    
    # Time-wasting
    'sporcle.com', 'quizilla.com', 'quizyourself.com', 'allthetests.com',
    'gotoquiz.com', 'zimbio.com', 'buzzfeed.com/quizzes', 'playbuzz.com',
    'personality-tests.org', 'psychologytoday.com/tests', 'quotev.com',
    'coolmathgames.com', 'candycrushsaga.com', 'angrybirdsonline.com',
    'crazygames.com', 'freeridegames.com', 'agame.com', 'bigfishgames.com',
    'popcap.com', 'zynga.com', 'pch.com', 'webkinz.com', 'neopets.com',
    'krazydad.com', 'jigsawplanet.com', 'jigidi.com', 'puzzlemaker.com',
    'crosswordcheats.com', 'sudoku.com', 'websudoku.com', 'printablesudoku.com',
    'mahjong.com', 'solitaire.com', 'pogo.com/solitaire', 'chessbase.com',
    'chess.com', 'lichess.org', 'checkers.com', 'playok.com', 'playhearts.com',
    'playcribbage.com', 'freegames.org', 'gamehouse.com', 'reflexive.com',
    'popcapgames.com', 'wildtangent.com', 'pchgames.com', 'zylom.com',
    'zapak.com', 'roiworld.com', 'newgrounds.com', 'armorgames.com',
    'onemorelevel.com', 'notdoppler.com', 'freegamesnetwork.com', 'gamesbox.com',
    'girlsgogames.com', 'girlgames.com', 'gamedistribution.com', 'addictinggames.com',
    'gamesofgondor.com', 'freeonlinegames.com', 'freeworldgroup.com',
    'flashgames247.com', 'mousebreaker.com', 'crazymonkeygames.com',
    'maxgames.com', 'juegos.com', 'juegosdiarios.com', 'paisdelosjuegos.com',
    'minijuegos.com', 'juegosjuegos.com', 'ojogos.com.br', 'jogos360.com.br',
    'yepi.com', 'kizi.com', 'frivol.com', 'paixnidia.gr', 'spielen.com',
    '1001spiele.de', 'gamestar.de', 'spela.se', 'spelletjes.nl', 'giochi.it',
    
    # Gambling
    'casino.com', 'pokerstars.com', 'bet365.com', 'draftkings.com', 'fanduel.com',
    'bovada.lv', 'williamhill.com', 'betway.com', 'bwin.com', '888casino.com',
    'casumo.com', 'leovegas.com', 'unibet.com', 'betfair.com', 'paddypower.com',
    'skybet.com', 'betonline.ag', 'mybookie.ag', 'sportsbetting.ag',
    'ladbrokes.com', 'coral.co.uk', 'betfred.com', 'betvictor.com', 'marathonbet.com',
    'pinnacle.com', 'betsson.com', 'netbet.com', 'mansion.com', 'mrgreen.com',
    'jackpotcity.com', 'royalvegas.com', 'spinpalace.com', 'rubyfortune.com',
    'gamingclub.com', 'partypoker.com', 'fulltilt.com', '888poker.com',
    'ggpoker.com', 'americascardroom.eu', 'ignitioncasino.eu', 'bodog.eu',
    'tigergaming.com', 'betfaircasino.com', 'sugarhouse.com', 'foxbet.com',
    'pointsbet.com', 'mgmresorts.com', 'caesars.com', 'harrahscasino.com',
    'goldennugget.com', 'borgataonline.com', 'tropicanacasino.com',
    'virginhotels.com', 'hardrockcasino.com', 'mohegansun.com', 'foxwoods.com',
    'winstar.com', 'pechanga.com', 'thunder-valley.com', 'palms.com',
    'montecarlo.com', 'bellagio.com', 'venetian.com', 'wynnlasvegas.com',
    'cosmopolitanlasvegas.com', 'aria.com', 'caesarspalace.com', 'mgmgrand.com',
    'mandalay-bay.com', 'luxor.com', 'excalibur.com', 'newyorknewyork.com',
    'circuscircus.com', 'flamingolasvegas.com', 'ballys.com', 'harrahs.com',
    'parislasvegas.com', 'riolasvegas.com', 'stratospherehotel.com', 'themirage.com',
    'treasureisland.com', 'goldennugget.com', 'orleanscasino.com', 'palms.com',
    'redrockcasino.com', 'greenvalleyranchresort.com', 'southpointcasino.com',
    'suncoastcasino.com', 'themresort.com', 'boylecasino.com', 'betsson.com',
    'casinoroom.com', 'comeon.com', 'dunder.com', 'karamba.com', 'mrgreen.com',
    'videoslots.com', 'slotsmillion.com', 'casumo.com', 'playojo.com',
    'partycasino.com', 'casino-x.com', 'joycasino.com', '1xslots.com',
    'betconstruct.com', 'casinoengine.com', 'goldenrace.com', 'isoftbet.com',
    'playtech.com', 'microgaming.co.uk', 'netent.com', 'evolution.com',
    'ezugi.com', 'pragmaticplay.com', 'yggdrasilgaming.com', 'playngo.com'
]

# Mega-expanded educational keywords
EDUCATIONAL_KEYWORDS = [
    # General education
    'learn', 'study', 'course', 'education', 'academic', 'tutorial',
    'research', 'science', 'history', 'mathematics', 'programming',
    'lecture', 'lesson', 'homework', 'university', 'college', 'school',
    'knowledge', 'experiment', 'thesis', 'theory', 'analysis', 'paper',
    'journal', 'article', 'resources', 'guide', 'materials', 'textbook',
    'curriculum', 'syllabus', 'assignment', 'project', 'class', 'workshop',
    'seminar', 'webinar', 'conference', 'symposium', 'training', 'certification',
    'degree', 'bachelor', 'master', 'phd', 'doctorate', 'faculty', 'professor',
    'instructor', 'teacher', 'student', 'scholar', 'library', 'digital library',
    'archive', 'database', 'repository', 'resource center', 'citation', 'reference',
    'bibliography', 'equation', 'formula', 'calculation', 'solution', 'problem set',
    'quiz', 'test', 'exam', 'assessment', 'evaluation', 'feedback', 'grade',
    'dataset', 'statistics', 'analytics', 'visualization', 'diagram', 'chart',
    'graph', 'map', 'timeline', 'engineering', 'architecture', 'medicine',
    'biology', 'chemistry', 'physics', 'geology', 'astronomy', 'psychology',
    'sociology', 'anthropology', 'economics', 'business', 'finance', 'accounting',
    'marketing', 'management', 'law', 'political science', 'philosophy',
    'literature', 'linguistics', 'language', 'translation', 'grammar', 'vocabulary',
    'dictionary', 'encyclopedia', 'thesaurus', 'glossary', 'definition',
    'explanation', 'demonstration', 'example', 'practice', 'exercise', 'skill',
    'technique', 'method', 'methodology', 'procedure', 'process', 'development',
    'innovation', 'discovery', 'invention', 'advancement', 'progress',
    
    # STEM fields
    'algorithm', 'computation', 'data structure', 'computational', 'mathematical',
    'algebraic', 'geometric', 'trigonometric', 'calculus', 'differential',
    'integral', 'vector', 'matrix', 'tensor', 'linear algebra', 'discrete math',
    'topology', 'number theory', 'combinatorics', 'probability', 'statistics',
    'regression', 'correlation', 'hypothesis', 'significance', 'confidence interval',
    'p-value', 'standard deviation', 'variance', 'mean', 'median', 'mode',
    'quantum', 'relativity', 'mechanics', 'dynamics', 'kinematics', 'statics',
    'thermodynamics', 'electromagnetism', 'optics', 'acoustics', 'fluid dynamics',
    'atomic', 'nuclear', 'particle', 'molecular', 'cellular', 'organic', 'inorganic',
    'biochemistry', 'biophysics', 'genetics', 'genomics', 'proteomics', 'ecology',
    'evolution', 'taxonomy', 'botany', 'zoology', 'microbiology', 'immunology',
    'neuroscience', 'anatomy', 'physiology', 'pathology', 'pharmacology',
    'toxicology', 'epidemiology', 'biostatistics', 'environmental science',
    'climate science', 'meteorology', 'oceanography', 'hydrology', 'seismology',
    'volcanology', 'mineralogy', 'petrology', 'geochemistry', 'paleontology',
    'cosmology', 'astrophysics', 'stellar', 'planetary', 'galactic', 'cosmic',
    'spacecraft', 'aeronautics', 'propulsion', 'materials science', 'nanotechnology',
    'biotechnology', 'robotics', 'artificial intelligence', 'machine learning',
    'deep learning', 'neural network', 'natural language processing', 'computer vision',
    'data mining', 'big data', 'data analysis', 'predictive modeling', 'simulation',
    'modeling', 'optimization', 'operations research', 'control theory',
    'cybernetics', 'systems theory', 'chaos theory', 'complexity theory',
    'network theory', 'game theory', 'decision theory', 'information theory',
    'cryptography', 'cybersecurity', 'computer architecture', 'operating system',
    'compiler', 'interpreter', 'assembly language', 'machine code', 'software engineering',
    'web development', 'database design', 'user interface', 'user experience',
    'human-computer interaction', 'virtual reality', 'augmented reality',
    
    # Humanities and social sciences
    'historiography', 'archaeology', 'paleography', 'numismatics', 'epigraphy',
    'philology', 'literary criticism', 'textual analysis', 'hermeneutics',
    'semiotics', 'structuralism', 'post-structuralism', 'deconstruction',
    'narratology', 'cultural studies', 'area studies', 'ethnic studies',
    'gender studies', 'queer theory', 'postcolonialism', 'orientalism',
    'occidentalism', 'marxism', 'critical theory', 'psychoanalysis',
    'discourse analysis', 'content analysis', 'conversation analysis',
    'ethnomethodology', 'phenomenology', 'existentialism', 'pragmatism',
    'empiricism', 'rationalism', 'idealism', 'materialism', 'dualism',
    'monism', 'determinism', 'compatibilism', 'libertarianism', 'utilitarianism',
    'deontology', 'virtue ethics', 'metaethics', 'normative ethics',
    'applied ethics', 'bioethics', 'environmental ethics', 'business ethics',
    'legal ethics', 'medical ethics', 'research ethics', 'political philosophy',
    'social contract', 'liberalism', 'conservatism', 'socialism', 'communism',
    'anarchism', 'fascism', 'nationalism', 'internationalism', 'globalization',
    'localization', 'federalism', 'unitarism', 'monarchy', 'oligarchy',
    'democracy', 'republic', 'autocracy', 'theocracy', 'geopolitics',
    'international relations', 'diplomacy', 'foreign policy', 'security studies',
    'peace studies', 'conflict resolution', 'development studies', 'public policy',
    'public administration', 'governance', 'macroeconomics', 'microeconomics',
    'econometrics', 'economic history', 'behavioral economics', 'development economics',
    'international economics', 'labor economics', 'health economics',
    'environmental economics', 'resource economics', 'industrial organization',
    'monetary policy', 'fiscal policy', 'taxation', 'public finance',
    'welfare economics', 'market structure', 'competition', 'monopoly',
    'oligopoly', 'perfect competition', 'imperfect competition', 'game theory',
    'social psychology', 'developmental psychology', 'cognitive psychology',
    'behavioral psychology', 'evolutionary psychology', 'positive psychology',
    'abnormal psychology', 'clinical psychology', 'counseling psychology',
    'educational psychology', 'industrial-organizational psychology',
    'health psychology', 'comparative psychology', 'psychophysics',
    'psycholinguistics', 'sociobiology', 'ethnography', 'ethnology',
    'cultural anthropology', 'social anthropology', 'linguistic anthropology',
    'physical anthropology', 'bioarchaeology', 'ethnohistory', 'folkloristics',
    'comparative mythology', 'urban studies', 'rural studies', 'demography',
    'human geography', 'cultural geography', 'political geography',
    'economic geography', 'historical geography', 'regional geography',
    
    # Specific educational content
    'tutorial', 'introduction to', 'fundamentals of', 'principles of',
    'basics of', 'essential', 'comprehensive guide', 'complete course',
    'in-depth', 'advanced', 'expert', 'mastering', 'professional', 'specialist',
    'beginner', 'intermediate', 'proficient', 'competent', 'skillful',
    'knowledgeable', 'understanding', 'learning path', 'roadmap', 'curriculum',
    'syllabus', 'learning objectives', 'learning outcomes', 'prerequisites',
    'requirements', 'recommended background', 'suggested readings',
    'supplementary materials', 'additional resources', 'further reading',
    'case study', 'case analysis', 'field study', 'empirical study',
    'qualitative research', 'quantitative research', 'mixed methods',
    'literature review', 'systematic review', 'meta-analysis', 'critical review',
    'analytical', 'theoretical framework', 'conceptual framework', 'paradigm',
    'hypothesis testing', 'null hypothesis', 'alternative hypothesis',
    'experimental design', 'control group', 'treatment group', 'independent variable',
    'dependent variable', 'confounding variable', 'random assignment',
    'random selection', 'sampling', 'population', 'representative sample',
    'convenience sample', 'snowball sampling', 'cluster sampling',
    'stratified sampling', 'longitudinal study', 'cross-sectional study',
    'correlational study', 'causal-comparative', 'experimental study',
    'quasi-experimental', 'true experimental', 'validity', 'reliability',
    'generalizability', 'transferability', 'credibility', 'confirmability',
    'triangulation', 'peer review', 'blind review', 'double-blind',
    'publication bias', 'replication crisis', 'p-hacking', 'harking',
    'researcher degrees of freedom', 'open science', 'reproducible research',
    'transparent methods', 'data sharing', 'preregistration', 'registered report'
]

# Mega-expanded entertainment keywords
ENTERTAINMENT_KEYWORDS = [
    # Social media trends and content
    'funny', 'prank', 'meme', 'joke', 'gaming', 'play', 'stream',
    'celebrity', 'gossip', 'viral', 'trend', 'challenge', 'react',
    'highlight', 'compilation', 'unboxing', 'review', 'reaction',
    'vlog', 'haul', 'asmr', 'mukbang', 'mukbanger', 'fail', 'epic',
    'awesome', 'amazing', 'incredible', 'shocking', 'unbelievable',
    'giveaway', 'exclusive', 'limited', 'premiere', 'trailer', 'teaser',
    'sneak peek', 'behind the scenes', 'bloopers', 'outtakes', 'deleted scenes',
    'top 10', 'countdown', 'clickbait', 'gamer', 'gameplay', 'walkthrough',
    'cheat', 'hack', 'mod', 'glitch', 'easter egg', 'speedrun', 'playthrough',
    'battle royale', 'multiplayer', 'pvp', 'co-op', 'esports', 'tournament',
    'championship', 'match', 'versus', 'squad', 'team', 'clan', 'guild',
    'alliance', 'faction', 'level up', 'grinding', 'farming', 'loot', 'drops',
    'skins', 'cosmetics', 'emotes', 'dance', 'costume', 'outfit', 'avatar',
    'character', 'profile', 'status', 'follower', 'following', 'friend',
    'unfriend', 'block', 'report', 'ban', 'mute', 'spam', 'troll', 'flame',
    'drama', 'beef', 'feud', 'controversy', 'canceled', 'exposed', 'tea',
    'spill', 'shade', 'rant', 'roast', 'diss', 'prank call', 'public prank',
    'social experiment', 'dare', 'challenge accepted', 'storytime', 'life hack',
    'diy fail', 'transformation', 'makeover', 'glow up', 'before and after',
    'fashion haul', 'try-on', 'lookbook', 'style', 'outfit of the day', 'ootd',
    'get ready with me', 'grwm', 'morning routine', 'night routine', 'skincare routine',
    'what i eat in a day', 'diet', 'weight loss', 'fitness challenge', 'workout routine',
    'relationship', 'dating', 'breakup', 'cheating', 'ex', 'crush', 'boyfriend',
    'girlfriend', 'couple goals', 'relationship goals', 'roommate', 'prank war',
    
    # Internet slang and trends
    'lol', 'rofl', 'lmao', 'yolo', 'fomo', 'tfw', 'mfw', 'irl', 'tbh', 'idk',
    'bff', 'gtg', 'brb', 'afk', 'omg', 'wtf', 'fyi', 'smh', 'tbt', 'wcw',
    'mcm', 'bae', 'savage', 'lit', 'fire', 'dope', 'on fleek', 'slay',
    'yasss', 'squad goals', 'mood', 'same', 'feels', 'vibes', 'aesthetic',
    'lowkey', 'highkey', 'sus', 'extra', 'basic', 'shook', 'triggered',
    'woke', 'stan', 'ship', 'otp', 'otw', 'gg', 'wp', 'ez', 'pog', 'poggers',
    'pepe', 'monkas', 'kappa', 'sadge', 'weirdchamp', 'pepega', 'catjam',
    'pepehands', 'pepelaugh', 'peeposad', 'lulw', 'xd', 'uwu', 'owo',
    'simp', 'incel', 'chad', 'karen', 'boomer', 'zoomer', 'doomer',
    'coomer', 'normie', 'cringe', 'based', 'redpilled', 'blackpilled',
    'cursed', 'blessed', 'blursed', 'copypasta', 'pasta', 'creepypasta',
    'wojak', 'npc', 'soyjak', 'dogeposting', 'shitposting', 'edgelord',
    'trollface', 'rickroll', 'stonks', 'not stonks', 'no cap', 'cap',
    'bet', 'glow up', 'ratio', 'mid', 'bussin', 'sheesh', 'yeet',
    
    # Gaming and streaming
    'fortnite', 'minecraft', 'among us', 'roblox', 'league of legends',
    'valorant', 'csgo', 'dota', 'apex legends', 'call of duty', 'warzone',
    'pubg', 'overwatch', 'rainbow six siege', 'rocket league', 'gta',
    'grand theft auto', 'fifa', 'madden', 'nba 2k', 'fall guys', 'animal crossing',
    'breath of the wild', 'pokemon', 'skyrim', 'world of warcraft', 'wow',
    'hearthstone', 'magic the gathering', 'arena', 'twitch', 'streamer',
    'subscriber', 'donation', 'bits', 'prime sub', 'raid', 'host', 'clip',
    'highlight', 'emote', 'chat', 'pogchamp', 'kappa', 'trihard', 'residentsleeper',
    'dansgame', 'jebaited', 'monkas', 'pepehands', 'lulw', 'omegalul',
    'speedrun', 'any%', '100%', 'glitchless', 'tool-assisted', 'tas',
    'rng', 'rta', 'segmented', 'meta', 'nerf', 'buff', 'patch', 'update',
    'dlc', 'expansion', 'season pass', 'battle pass', 'microtransaction',
    'loot box', 'skin', 'cosmetic', 'mod', 'addon', 'texture pack',
    'resource pack', 'shader', 'lag', 'ping', 'fps', 'frame rate', 'graphics',
    'resolution', 'rendering', 'ray tracing', 'vsync', 'anti-aliasing',
    'fov', 'field of view', 'mouse sensitivity', 'keybinds', 'controller',
    'keyboard', 'gaming mouse', 'gaming keyboard', 'gaming chair',
    'gaming setup', 'gaming pc', 'gaming laptop', 'gpu', 'cpu', 'ram',
    'rgb', 'overclock', 'benchmark', 'performance', 'optimization',
    
    # Entertainment media
    'movie', 'film', 'tv show', 'television', 'series', 'season', 'episode',
    'binge-watch', 'marathon', 'stream', 'netflix', 'hulu', 'disney plus',
    'prime video', 'hbo max', 'peacock', 'paramount plus', 'crunchyroll',
    'funimation', 'anime', 'manga', 'webtoon', 'comic', 'novel', 'book series',
    'fiction', 'fantasy', 'sci-fi', 'science fiction', 'horror', 'thriller',
    'mystery', 'action', 'adventure', 'romance', 'drama', 'comedy', 'sitcom',
    'documentary', 'reality tv', 'game show', 'talk show', 'late night',
    'variety show', 'podcast', 'radio show', 'soundtrack', 'score', 'theme song',
    'opening', 'ending', 'character', 'protagonist', 'antagonist', 'villain',
    'hero', 'antihero', 'plot', 'story', 'narrative', 'arc', 'universe',
    'canon', 'fanon', 'spin-off', 'reboot', 'remake', 'adaptation', 'sequel',
    'prequel', 'trilogy', 'saga', 'franchise', 'cinematic universe',
    'shared universe', 'crossover', 'easter egg', 'cameo', 'reference',
    'homage', 'parody', 'spoof', 'satire', 'comedic', 'dramatic', 'suspenseful',
    'cliffhanger', 'twist', 'reveal', 'spoiler', 'leak', 'rumor', 'theory',
    'fan theory', 'headcanon', 'fanfiction', 'fanart', 'cosplay', 'convention',
    'con', 'panel', 'autograph', 'meet and greet', 'photo op', 'merch', 'collectible',
    'figurine', 'poster', 'soundtrack', 'ost', 'score', 'composer',
    
    # Celebrity and pop culture
    'celebrity', 'star', 'famous', 'actor', 'actress', 'director', 'producer',
    'writer', 'singer', 'rapper', 'musician', 'band', 'artist', 'influencer',
    'youtuber', 'content creator', 'tiktoker', 'instagrammer', 'model',
    'fashion', 'style', 'trend', 'designer', 'brand', 'collection', 'line',
    'collaboration', 'collab', 'sponsor', 'endorsement', 'ambassador',
    'spokesperson', 'commercial', 'advertisement', 'ad', 'sponsored',
    'partnership', 'paparazzi', 'tabloid', 'gossip', 'rumor', 'scandal',
    'controversy', 'drama', 'tea', 'feud', 'beef', 'diss', 'callout',
    'exposed', 'canceled', 'cancel culture', 'problematic', 'apology',
    'statement', 'interview', 'exclusive', 'tell-all', 'memoir', 'biography',
    'documentary', 'behind the scenes', 'making of', 'bloopers', 'gag reel',
    'red carpet', 'premiere', 'award show', 'awards', 'nomination', 'nominee',
    'winner', 'acceptance speech', 'host', 'presenter', 'performance',
    'live show', 'concert', 'tour', 'festival', 'gig', 'album', 'single',
    'track', 'release', 'drop', 'leak', 'chart', 'billboard', 'number one',
    'top ten', 'hit', 'flop', 'comeback', 'debut', 'breakout', 'viral',
    'trending', 'fan', 'fanbase', 'fandom', 'stan', 'hater', 'critic',    # Entertainment (continued)
    'giantbomb.com', 'gamespot.com',
    'n4g.com', 'pushsquare.com', 'nintendolife.com', 'gamereactor.eu',
    'dualshockers.com', 'playstationlifestyle.net', 'xboxachievements.com',
    'trueachievements.com', 'psnprofiles.com', 'retronauts.com',
    
    # Shopping/Browsing
    'amazon.com/browse', 'ebay.com/browse', 'walmart.com/browse', 'target.com/browse',
    'wish.com', 'aliexpress.com', 'etsy.com/browse', 'shein.com', 'fashionnova.com',
    'zara.com', 'hm.com', 'forever21.com', 'asos.com', 'nordstrom.com', 'macys.com',
    'bestbuy.com/browse', 'newegg.com/browse', 'wayfair.com', 'ikea.com/browse',
    'homedepot.com/browse', 'lowes.com/browse', 'sephora.com', 'ulta.com',
    'shopify.com', 'wix.com/shopping', 'overstock.com', 'jcpenney.com',
    'kohls.com', 'costco.com', 'samsclub.com', 'bjs.com', 'tjmaxx.com',
    'marshalls.com', 'homegoods.com', 'pier1.com', 'crateandbarrel.com',
    'cb2.com', 'potterybarn.com', 'westelm.com', 'anthropologie.com',
    'urbanoutfitters.com', 'freepeople.com', 'loft.com', 'anntaylor.com',
    'gap.com', 'oldnavy.com', 'abercrombie.com', 'ae.com', 'hollisterco.com',
    'uniqlo.com', 'lululemon.com', 'athleta.com', 'nike.com', 'adidas.com',
    'underarmour.com', 'puma.com', 'reebok.com', 'newbalance.com', 'converse.com',
    'vans.com', 'timberland.com', 'drmartens.com', 'crocs.com', 'ugg.com',
    'skechers.com', 'clarks.com', 'ninewest.com', 'stevemadden.com',
    'stuartweitzman.com', 'jimmychoo.com', 'manoloblahnik.com', 'louboutin.com',
    'gucci.com', 'louisvuitton.com', 'prada.com', 'chanel.com', 'dior.com',
    'burberry.com', 'versace.com', 'armani.com', 'calvinklein.com', 'tommyhilfiger.com',
    'ralphlauren.com', 'michaelkors.com', 'coach.com', 'katespade.com',
    'toryburch.com', 'marcjacobs.com', 'valentino.com', 'balenciaga.com',
    'fendi.com', 'hermes.com', 'tiffany.com', 'pandora.net', 'swarovski.com',
    'cartier.com', 'bulgari.com', 'rolex.com', 'omega.com', 'tagheuer.com',
    
    # Time-wasting
    'sporcle.com', 'quizilla.com', 'quizyourself.com', 'allthetests.com',
    'gotoquiz.com', 'zimbio.com', 'buzzfeed.com/quizzes', 'playbuzz.com',
    'personality-tests.org', 'psychologytoday.com/tests', 'quotev.com',
    'coolmathgames.com', 'candycrushsaga.com', 'angrybirdsonline.com',
    'crazygames.com', 'freeridegames.com', 'agame.com', 'bigfishgames.com',
    'popcap.com', 'zynga.com', 'pch.com', 'webkinz.com', 'neopets.com',
    'krazydad.com', 'jigsawplanet.com', 'jigidi.com', 'puzzlemaker.com',
    'crosswordcheats.com', 'sudoku.com', 'websudoku.com', 'printablesudoku.com',
    'mahjong.com', 'solitaire.com', 'pogo.com/solitaire', 'chessbase.com',
    'chess.com', 'lichess.org', 'checkers.com', 'playok.com', 'playhearts.com',
    'playcribbage.com', 'freegames.org', 'gamehouse.com', 'reflexive.com',
    'popcapgames.com', 'wildtangent.com', 'pchgames.com', 'zylom.com',
    'zapak.com', 'roiworld.com', 'newgrounds.com', 'armorgames.com',
    'onemorelevel.com', 'notdoppler.com', 'freegamesnetwork.com', 'gamesbox.com',
    'girlsgogames.com', 'girlgames.com', 'gamedistribution.com', 'addictinggames.com',
    'gamesofgondor.com', 'freeonlinegames.com', 'freeworldgroup.com',
    'flashgames247.com', 'mousebreaker.com', 'crazymonkeygames.com',
    'maxgames.com', 'juegos.com', 'juegosdiarios.com', 'paisdelosjuegos.com',
    'minijuegos.com', 'juegosjuegos.com', 'ojogos.com.br', 'jogos360.com.br',
    'yepi.com', 'kizi.com', 'frivol.com', 'paixnidia.gr', 'spielen.com',
    '1001spiele.de', 'gamestar.de', 'spela.se', 'spelletjes.nl', 'giochi.it',
    
    # Gambling
    'casino.com', 'pokerstars.com', 'bet365.com', 'draftkings.com', 'fanduel.com',
    'bovada.lv', 'williamhill.com', 'betway.com', 'bwin.com', '888casino.com',
    'casumo.com', 'leovegas.com', 'unibet.com', 'betfair.com', 'paddypower.com',
    'skybet.com', 'betonline.ag', 'mybookie.ag', 'sportsbetting.ag',
    'ladbrokes.com', 'coral.co.uk', 'betfred.com', 'betvictor.com', 'marathonbet.com',
    'pinnacle.com', 'betsson.com', 'netbet.com', 'mansion.com', 'mrgreen.com',
    'jackpotcity.com', 'royalvegas.com', 'spinpalace.com', 'rubyfortune.com',
    'gamingclub.com', 'partypoker.com', 'fulltilt.com', '888poker.com',
    'ggpoker.com', 'americascardroom.eu', 'ignitioncasino.eu', 'bodog.eu',
    'tigergaming.com', 'betfaircasino.com', 'sugarhouse.com', 'foxbet.com',
    'pointsbet.com', 'mgmresorts.com', 'caesars.com', 'harrahscasino.com',
    'goldennugget.com', 'borgataonline.com', 'tropicanacasino.com',
    'virginhotels.com', 'hardrockcasino.com', 'mohegansun.com', 'foxwoods.com',
    'winstar.com', 'pechanga.com', 'thunder-valley.com', 'palms.com',
    'montecarlo.com', 'bellagio.com', 'venetian.com', 'wynnlasvegas.com',
    'cosmopolitanlasvegas.com', 'aria.com', 'caesarspalace.com', 'mgmgrand.com',
    'mandalay-bay.com', 'luxor.com', 'excalibur.com', 'newyorknewyork.com',
    'circuscircus.com', 'flamingolasvegas.com', 'ballys.com', 'harrahs.com',
    'parislasvegas.com', 'riolasvegas.com', 'stratospherehotel.com', 'themirage.com',
    'treasureisland.com', 'goldennugget.com', 'orleanscasino.com', 'palms.com',
    'redrockcasino.com', 'greenvalleyranchresort.com', 'southpointcasino.com',
    'suncoastcasino.com', 'themresort.com', 'boylecasino.com', 'betsson.com',
    'casinoroom.com', 'comeon.com', 'dunder.com', 'karamba.com', 'mrgreen.com',
    'videoslots.com', 'slotsmillion.com', 'casumo.com', 'playojo.com',
    'partycasino.com', 'casino-x.com', 'joycasino.com', '1xslots.com',
    'betconstruct.com', 'casinoengine.com', 'goldenrace.com', 'isoftbet.com',
    'playtech.com', 'microgaming.co.uk', 'netent.com', 'evolution.com',
    'ezugi.com', 'pragmaticplay.com', 'yggdrasilgaming.com', 'playngo.com'
]

# Mega-expanded educational keywords
EDUCATIONAL_KEYWORDS = [
    # General education
    'learn', 'study', 'course', 'education', 'academic', 'tutorial',
    'research', 'science', 'history', 'mathematics', 'programming',
    'lecture', 'lesson', 'homework', 'university', 'college', 'school',
    'knowledge', 'experiment', 'thesis', 'theory', 'analysis', 'paper',
    'journal', 'article', 'resources', 'guide', 'materials', 'textbook',
    'curriculum', 'syllabus', 'assignment', 'project', 'class', 'workshop',
    'seminar', 'webinar', 'conference', 'symposium', 'training', 'certification',
    'degree', 'bachelor', 'master', 'phd', 'doctorate', 'faculty', 'professor',
    'instructor', 'teacher', 'student', 'scholar', 'library', 'digital library',
    'archive', 'database', 'repository', 'resource center', 'citation', 'reference',
    'bibliography', 'equation', 'formula', 'calculation', 'solution', 'problem set',
    'quiz', 'test', 'exam', 'assessment', 'evaluation', 'feedback', 'grade',
    'dataset', 'statistics', 'analytics', 'visualization', 'diagram', 'chart',
    'graph', 'map', 'timeline', 'engineering', 'architecture', 'medicine',
    'biology', 'chemistry', 'physics', 'geology', 'astronomy', 'psychology',
    'sociology', 'anthropology', 'economics', 'business', 'finance', 'accounting',
    'marketing', 'management', 'law', 'political science', 'philosophy',
    'literature', 'linguistics', 'language', 'translation', 'grammar', 'vocabulary',
    'dictionary', 'encyclopedia', 'thesaurus', 'glossary', 'definition',
    'explanation', 'demonstration', 'example', 'practice', 'exercise', 'skill',
    'technique', 'method', 'methodology', 'procedure', 'process', 'development',
    'innovation', 'discovery', 'invention', 'advancement', 'progress',
    
    # STEM fields
    'algorithm', 'computation', 'data structure', 'computational', 'mathematical',
    'algebraic', 'geometric', 'trigonometric', 'calculus', 'differential',
    'integral', 'vector', 'matrix', 'tensor', 'linear algebra', 'discrete math',
    'topology', 'number theory', 'combinatorics', 'probability', 'statistics',
    'regression', 'correlation', 'hypothesis', 'significance', 'confidence interval',
    'p-value', 'standard deviation', 'variance', 'mean', 'median', 'mode',
    'quantum', 'relativity', 'mechanics', 'dynamics', 'kinematics', 'statics',
    'thermodynamics', 'electromagnetism', 'optics', 'acoustics', 'fluid dynamics',
    'atomic', 'nuclear', 'particle', 'molecular', 'cellular', 'organic', 'inorganic',
    'biochemistry', 'biophysics', 'genetics', 'genomics', 'proteomics', 'ecology',
    'evolution', 'taxonomy', 'botany', 'zoology', 'microbiology', 'immunology',
    'neuroscience', 'anatomy', 'physiology', 'pathology', 'pharmacology',
    'toxicology', 'epidemiology', 'biostatistics', 'environmental science',
    'climate science', 'meteorology', 'oceanography', 'hydrology', 'seismology',
    'volcanology', 'mineralogy', 'petrology', 'geochemistry', 'paleontology',
    'cosmology', 'astrophysics', 'stellar', 'planetary', 'galactic', 'cosmic',
    'spacecraft', 'aeronautics', 'propulsion', 'materials science', 'nanotechnology',
    'biotechnology', 'robotics', 'artificial intelligence', 'machine learning',
    'deep learning', 'neural network', 'natural language processing', 'computer vision',
    'data mining', 'big data', 'data analysis', 'predictive modeling', 'simulation',
    'modeling', 'optimization', 'operations research', 'control theory',
    'cybernetics', 'systems theory', 'chaos theory', 'complexity theory',
    'network theory', 'game theory', 'decision theory', 'information theory',
    'cryptography', 'cybersecurity', 'computer architecture', 'operating system',
    'compiler', 'interpreter', 'assembly language', 'machine code', 'software engineering',
    'web development', 'database design', 'user interface', 'user experience',
    'human-computer interaction', 'virtual reality', 'augmented reality',
    
    # Humanities and social sciences
    'historiography', 'archaeology', 'paleography', 'numismatics', 'epigraphy',
    'philology', 'literary criticism', 'textual analysis', 'hermeneutics',
    'semiotics', 'structuralism', 'post-structuralism', 'deconstruction',
    'narratology', 'cultural studies', 'area studies', 'ethnic studies',
    'gender studies', 'queer theory', 'postcolonialism', 'orientalism',
    'occidentalism', 'marxism', 'critical theory', 'psychoanalysis',
    'discourse analysis', 'content analysis', 'conversation analysis',
    'ethnomethodology', 'phenomenology', 'existentialism', 'pragmatism',
    'empiricism', 'rationalism', 'idealism', 'materialism', 'dualism',
    'monism', 'determinism', 'compatibilism', 'libertarianism', 'utilitarianism',
    'deontology', 'virtue ethics', 'metaethics', 'normative ethics',
    'applied ethics', 'bioethics', 'environmental ethics', 'business ethics',
    'legal ethics', 'medical ethics', 'research ethics', 'political philosophy',
    'social contract', 'liberalism', 'conservatism', 'socialism', 'communism',
    'anarchism', 'fascism', 'nationalism', 'internationalism', 'globalization',
    'localization', 'federalism', 'unitarism', 'monarchy', 'oligarchy',
    'democracy', 'republic', 'autocracy', 'theocracy', 'geopolitics',
    'international relations', 'diplomacy', 'foreign policy', 'security studies',
    'peace studies', 'conflict resolution', 'development studies', 'public policy',
    'public administration', 'governance', 'macroeconomics', 'microeconomics',
    'econometrics', 'economic history', 'behavioral economics', 'development economics',
    'international economics', 'labor economics', 'health economics',
    'environmental economics', 'resource economics', 'industrial organization',
    'monetary policy', 'fiscal policy', 'taxation', 'public finance',
    'welfare economics', 'market structure', 'competition', 'monopoly',
    'oligopoly', 'perfect competition', 'imperfect competition', 'game theory',
    'social psychology', 'developmental psychology', 'cognitive psychology',
    'behavioral psychology', 'evolutionary psychology', 'positive psychology',
    'abnormal psychology', 'clinical psychology', 'counseling psychology',
    'educational psychology', 'industrial-organizational psychology',
    'health psychology', 'comparative psychology', 'psychophysics',
    'psycholinguistics', 'sociobiology', 'ethnography', 'ethnology',
    'cultural anthropology', 'social anthropology', 'linguistic anthropology',
    'physical anthropology', 'bioarchaeology', 'ethnohistory', 'folkloristics',
    'comparative mythology', 'urban studies', 'rural studies', 'demography',
    'human geography', 'cultural geography', 'political geography',
    'economic geography', 'historical geography', 'regional geography',
    
    # Specific educational content
    'tutorial', 'introduction to', 'fundamentals of', 'principles of',
    'basics of', 'essential', 'comprehensive guide', 'complete course',
    'in-depth', 'advanced', 'expert', 'mastering', 'professional', 'specialist',
    'beginner', 'intermediate', 'proficient', 'competent', 'skillful',
    'knowledgeable', 'understanding', 'learning path', 'roadmap', 'curriculum',
    'syllabus', 'learning objectives', 'learning outcomes', 'prerequisites',
    'requirements', 'recommended background', 'suggested readings',
    'supplementary materials', 'additional resources', 'further reading',
    'case study', 'case analysis', 'field study', 'empirical study',
    'qualitative research', 'quantitative research', 'mixed methods',
    'literature review', 'systematic review', 'meta-analysis', 'critical review',
    'analytical', 'theoretical framework', 'conceptual framework', 'paradigm',
    'hypothesis testing', 'null hypothesis', 'alternative hypothesis',
    'experimental design', 'control group', 'treatment group', 'independent variable',
    'dependent variable', 'confounding variable', 'random assignment',
    'random selection', 'sampling', 'population', 'representative sample',
    'convenience sample', 'snowball sampling', 'cluster sampling',
    'stratified sampling', 'longitudinal study', 'cross-sectional study',
    'correlational study', 'causal-comparative', 'experimental study',
    'quasi-experimental', 'true experimental', 'validity', 'reliability',
    'generalizability', 'transferability', 'credibility', 'confirmability',
    'triangulation', 'peer review', 'blind review', 'double-blind',
    'publication bias', 'replication crisis', 'p-hacking', 'harking',
    'researcher degrees of freedom', 'open science', 'reproducible research',
    'transparent methods', 'data sharing', 'preregistration', 'registered report'
]

# Mega-expanded entertainment keywords
ENTERTAINMENT_KEYWORDS = [
    # Social media trends and content
    'funny', 'prank', 'meme', 'joke', 'gaming', 'play', 'stream',
    'celebrity', 'gossip', 'viral', 'trend', 'challenge', 'react',
    'highlight', 'compilation', 'unboxing', 'review', 'reaction',
    'vlog', 'haul', 'asmr', 'mukbang', 'mukbanger', 'fail', 'epic',
    'awesome', 'amazing', 'incredible', 'shocking', 'unbelievable',
    'giveaway', 'exclusive', 'limited', 'premiere', 'trailer', 'teaser',
    'sneak peek', 'behind the scenes', 'bloopers', 'outtakes', 'deleted scenes',
    'top 10', 'countdown', 'clickbait', 'gamer', 'gameplay', 'walkthrough',
    'cheat', 'hack', 'mod', 'glitch', 'easter egg', 'speedrun', 'playthrough',
    'battle royale', 'multiplayer', 'pvp', 'co-op', 'esports', 'tournament',
    'championship', 'match', 'versus', 'squad', 'team', 'clan', 'guild',
    'alliance', 'faction', 'level up', 'grinding', 'farming', 'loot', 'drops',
    'skins', 'cosmetics', 'emotes', 'dance', 'costume', 'outfit', 'avatar',
    'character', 'profile', 'status', 'follower', 'following', 'friend',
    'unfriend', 'block', 'report', 'ban', 'mute', 'spam', 'troll', 'flame',
    'drama', 'beef', 'feud', 'controversy', 'canceled', 'exposed', 'tea',
    'spill', 'shade', 'rant', 'roast', 'diss', 'prank call', 'public prank',
    'social experiment', 'dare', 'challenge accepted', 'storytime', 'life hack',
    'diy fail', 'transformation', 'makeover', 'glow up', 'before and after',
    'fashion haul', 'try-on', 'lookbook', 'style', 'outfit of the day', 'ootd',
    'get ready with me', 'grwm', 'morning routine', 'night routine', 'skincare routine',
    'what i eat in a day', 'diet', 'weight loss', 'fitness challenge', 'workout routine',
    'relationship', 'dating', 'breakup', 'cheating', 'ex', 'crush', 'boyfriend',
    'girlfriend', 'couple goals', 'relationship goals', 'roommate', 'prank war',
    
    # Internet slang and trends
    'lol', 'rofl', 'lmao', 'yolo', 'fomo', 'tfw', 'mfw', 'irl', 'tbh', 'idk',
    'bff', 'gtg', 'brb', 'afk', 'omg', 'wtf', 'fyi', 'smh', 'tbt', 'wcw',
    'mcm', 'bae', 'savage', 'lit', 'fire', 'dope', 'on fleek', 'slay',
    'yasss', 'squad goals', 'mood', 'same', 'feels', 'vibes', 'aesthetic',
    'lowkey', 'highkey', 'sus', 'extra', 'basic', 'shook', 'triggered',
    'woke', 'stan', 'ship', 'otp', 'otw', 'gg', 'wp', 'ez', 'pog', 'poggers',
    'pepe', 'monkas', 'kappa', 'sadge', 'weirdchamp', 'pepega', 'catjam',
    'pepehands', 'pepelaugh', 'peeposad', 'lulw', 'xd', 'uwu', 'owo',
    'simp', 'incel', 'chad', 'karen', 'boomer', 'zoomer', 'doomer',
    'coomer', 'normie', 'cringe', 'based', 'redpilled', 'blackpilled',
    'cursed', 'blessed', 'blursed', 'copypasta', 'pasta', 'creepypasta',
    'wojak', 'npc', 'soyjak', 'dogeposting', 'shitposting', 'edgelord',
    'trollface', 'rickroll', 'stonks', 'not stonks', 'no cap', 'cap',
    'bet', 'glow up', 'ratio', 'mid', 'bussin', 'sheesh', 'yeet',
    
    # Gaming and streaming
    'fortnite', 'minecraft', 'among us', 'roblox', 'league of legends',
    'valorant', 'csgo', 'dota', 'apex legends', 'call of duty', 'warzone',
    'pubg', 'overwatch', 'rainbow six siege', 'rocket league', 'gta',
    'grand theft auto', 'fifa', 'madden', 'nba 2k', 'fall guys', 'animal crossing',
    'breath of the wild', 'pokemon', 'skyrim', 'world of warcraft', 'wow',
    'hearthstone', 'magic the gathering', 'arena', 'twitch', 'streamer',
    'subscriber', 'donation', 'bits', 'prime sub', 'raid', 'host', 'clip',
    'highlight', 'emote', 'chat', 'pogchamp', 'kappa', 'trihard', 'residentsleeper',
    'dansgame', 'jebaited', 'monkas', 'pepehands', 'lulw', 'omegalul',
    'speedrun', 'any%', '100%', 'glitchless', 'tool-assisted', 'tas',
    'rng', 'rta', 'segmented', 'meta', 'nerf', 'buff', 'patch', 'update',
    'dlc', 'expansion', 'season pass', 'battle pass', 'microtransaction',
    'loot box', 'skin', 'cosmetic', 'mod', 'addon', 'texture pack',
    'resource pack', 'shader', 'lag', 'ping', 'fps', 'frame rate', 'graphics',
    'resolution', 'rendering', 'ray tracing', 'vsync', 'anti-aliasing',
    'fov', 'field of view', 'mouse sensitivity', 'keybinds', 'controller',
    'keyboard', 'gaming mouse', 'gaming keyboard', 'gaming chair',
    'gaming setup', 'gaming pc', 'gaming laptop', 'gpu', 'cpu', 'ram',
    'rgb', 'overclock', 'benchmark', 'performance', 'optimization',
    
    # Entertainment media
    'movie', 'film', 'tv show', 'television', 'series', 'season', 'episode',
    'binge-watch', 'marathon', 'stream', 'netflix', 'hulu', 'disney plus',
    'prime video', 'hbo max', 'peacock', 'paramount plus', 'crunchyroll',
    'funimation', 'anime', 'manga', 'webtoon', 'comic', 'novel', 'book series',
    'fiction', 'fantasy', 'sci-fi', 'science fiction', 'horror', 'thriller',
    'mystery', 'action', 'adventure', 'romance', 'drama', 'comedy', 'sitcom',
    'documentary', 'reality tv', 'game show', 'talk show', 'late night',
    'variety show', 'podcast', 'radio show', 'soundtrack', 'score', 'theme song',
    'opening', 'ending', 'character', 'protagonist', 'antagonist', 'villain',
    'hero', 'antihero', 'plot', 'story', 'narrative', 'arc', 'universe',
    'canon', 'fanon', 'spin-off', 'reboot', 'remake', 'adaptation', 'sequel',
    'prequel', 'trilogy', 'saga', 'franchise', 'cinematic universe',
    'shared universe', 'crossover', 'easter egg', 'cameo', 'reference',
    'homage', 'parody', 'spoof', 'satire', 'comedic', 'dramatic', 'suspenseful',
    'cliffhanger', 'twist', 'reveal', 'spoiler', 'leak', 'rumor', 'theory',
    'fan theory', 'headcanon', 'fanfiction', 'fanart', 'cosplay', 'convention',
    'con', 'panel', 'autograph', 'meet and greet', 'photo op', 'merch', 'collectible',
    'figurine', 'poster', 'soundtrack', 'ost', 'score', 'composer',
    
    # Celebrity and pop culture
    'celebrity', 'star', 'famous', 'actor', 'actress', 'director', 'producer',
    'writer', 'singer', 'rapper', 'musician', 'band', 'artist', 'influencer',
    'youtuber', 'content creator', 'tiktoker', 'instagrammer', 'model',
    'fashion', 'style', 'trend', 'designer', 'brand', 'collection', 'line',
    'collaboration', 'collab', 'sponsor', 'endorsement', 'ambassador',
    'spokesperson', 'commercial', 'advertisement', 'ad', 'sponsored',
    'partnership', 'paparazzi', 'tabloid', 'gossip', 'rumor', 'scandal',
    'controversy', 'drama', 'tea', 'feud', 'beef', 'diss', 'callout',
    'exposed', 'canceled', 'cancel culture', 'problematic', 'apology',
    'statement', 'interview', 'exclusive', 'tell-all', 'memoir', 'biography',
    'documentary', 'behind the scenes', 'making of', 'bloopers', 'gag reel',
    'red carpet', 'premiere', 'award show', 'awards', 'nomination', 'nominee',
    'winner', 'acceptance speech', 'host', 'presenter', 'performance',
    'live show', 'concert', 'tour', 'festival', 'gig', 'album', 'single',
    'track', 'release', 'drop', 'leak', 'chart', 'billboard', 'number one',
    'top ten', 'hit', 'flop', 'comeback', 'debut', 'breakout', 'viral',
    'trending', 'fan', 'fanbase', 'fandom', 'stan', 'hater', 'critic',
            
    # Celebrity and pop culture (continued)
    'review', 'rating', 'score', 'critique', 'reception', 'success', 'failure',
    'blockbuster', 'box office', 'ratings', 'viewership', 'audience', 'demographic',
    'target audience', 'fanservice', 'mainstream', 'underground', 'indie', 'pop',
    'popular', 'cult classic', 'cult following', 'fan favorite', 'critically acclaimed',
    
    # Sports and recreation entertainment
    'sports', 'game', 'match', 'tournament', 'championship', 'league', 'season',
    'playoff', 'finals', 'world cup', 'olympics', 'medal', 'champion', 'title',
    'record', 'streak', 'highlight', 'replay', 'slow motion', 'referee', 'umpire',
    'call', 'penalty', 'foul', 'red card', 'yellow card', 'touchdown', 'goal',
    'basket', 'home run', 'grand slam', 'ace', 'strike', 'ball', 'out', 'save',
    'block', 'tackle', 'dunk', 'three-pointer', 'buzzer beater', 'overtime',
    'sudden death', 'injury', 'bench', 'substitute', 'starter', 'draft',
    'trade', 'free agent', 'contract', 'salary', 'cap', 'luxury tax',
    'coach', 'manager', 'team', 'player', 'rookie', 'veteran', 'hall of fame',
    'legend', 'goat', 'mvp', 'all-star', 'pro bowl', 'all-pro', 'fantasy sports',
    'fantasy football', 'fantasy basketball', 'fantasy baseball', 'betting',
    'odds', 'spread', 'over/under', 'parlay', 'prop bet', 'sportsbook',
    
    # Internet culture and memes
    'meme', 'viral', 'trending', 'challenge', 'tag', 'hashtag', 'caption',
    'relatable', 'reaction image', 'reaction gif', 'image macro', 'template',
    'format', 'photoshop', 'edit', 'deep fried', 'cursed', 'blessed', 'blursed',
    'wholesome', 'dank', 'normie', 'shitpost', 'repost', 'oc', 'original content',
    'crosspost', 'upvote', 'downvote', 'award', 'gold', 'silver', 'platinum',
    'karma', 'thread', 'subreddit', 'moderator', 'admin', 'ban', 'shadowban',
    'censor', 'removed', 'deleted', 'locked', 'controversial', 'political',
    'satire', 'parody', 'irony', 'sarcasm', 'bait', 'trolling', 'flame war',
    'rage comic', 'advice animal', 'demotivational', 'wojak', 'pepe', 'doge',
    'stonks', 'chad', 'virgin', 'vs', 'alignment chart', 'starter pack',
    'expectation vs reality', 'expanding brain', 'drake', 'distracted boyfriend',
    'change my mind', "they don't know", 'always has been', 'nobody:',
    'corporate needs you to find the difference', 'what if i told you',
    'one does not simply', "i don't always", 'but when i do', 'surprised pikachu',
    'this is fine', 'stonks', 'not stonks', 'confused screaming',
    'confused math lady', "wait, that's illegal", 'listen here you little',
    'i see this as an absolute win', 'reality can be whatever i want',
    "i've won, but at what cost", "you wouldn't get it", "understandable have a nice day",
    "i'm about to end this man's whole career", 'destruction 100', 'speech 100',
    'restoration 100', 'stop it, get some help', 'thomas had never seen such bullshit',
    'visible confusion', "i'll ignore that", 'press f to pay respects',
    'why are you running', 'look how they massacred my boy', 'well yes, but actually no',
    "it ain't much, but it's honest work", 'say sike right now', 'perhaps',
    'ah shit, here we go again', "i'm gonna do what's called a pro gamer move",
    
    # Food and lifestyle entertainment
    'food', 'recipe', 'cooking', 'baking', 'chef', 'cook', 'culinary', 'cuisine',
    'restaurant', 'dining', 'meal', 'breakfast', 'lunch', 'dinner', 'brunch',
    'appetizer', 'entree', 'dessert', 'snack', 'gourmet', 'foodie', 'food porn',
    'plating', 'presentation', 'tasty', 'delicious', 'yummy', 'flavor', 'texture',
    'aroma', 'spicy', 'sweet', 'savory', 'umami', 'bitter', 'sour', 'creamy',
    'crunchy', 'juicy', 'tender', 'diet', 'keto', 'paleo', 'vegan', 'vegetarian',
    'gluten-free', 'dairy-free', 'organic', 'non-gmo', 'all-natural', 'clean eating',
    'intermittent fasting', 'cheat day', 'meal prep', 'cooking show', 'cooking channel',
    'cooking tutorial', 'recipe video', 'asmr cooking', 'mukbang', 'eating challenge',
    'eating competition', 'food challenge', 'spicy challenge', 'hot sauce challenge',
    'sour candy challenge', 'blind taste test', 'mystery food', 'weird food', 'exotic food',
    'international cuisine', 'foreign food', 'local cuisine', 'traditional food',
    'family recipe', 'secret recipe', 'homemade', 'from scratch', 'quick and easy',
    '5-minute recipe', 'one-pot meal', 'no-bake', 'microwave recipe', 'instant pot',
    'air fryer', 'slow cooker', 'cocktail', 'mixed drink', 'bartender', 'mixology',
    'wine', 'beer', 'spirits', 'whiskey', 'vodka', 'gin', 'rum', 'tequila',
    'liqueur', 'shot', 'drink recipe', 'home bar', 'drunk', 'tipsy', 'hangover',
    'lifestyle', 'fashion', 'beauty', 'makeup', 'skincare', 'haircare', 'style',
    'outfit', 'look', 'makeover', 'transformation', 'glow up', 'before and after',
    'haul', 'collection', 'routine', 'tutorial', 'get ready with me', 'grwm',
    'morning routine', 'night routine', 'skincare routine', 'makeup routine',
    'hair tutorial', 'nail art', 'manicure', 'pedicure', 'facial', 'spa day',
    'self-care', 'pamper', 'relax', 'destress', 'meditation', 'yoga', 'workout',
    'exercise', 'fitness', 'gym', 'home workout', 'cardio', 'strength training',
    'weights', 'hiit', 'pilates', 'crossfit', 'bodybuilding', 'transform', 'weight loss',
    'diet', 'nutrition', 'calorie', 'macro', 'protein', 'carbs', 'fat',
    'supplement', 'vitamins', 'minerals', 'pre-workout', 'post-workout',
    'progress', 'journey', 'motivation', 'inspiration', 'goals', 'challenge'
]

def extract_domain(url):
    """Extract the domain from a URL."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def check_known_domains(url):
    """Check if the URL belongs to known productive or unproductive domains."""
    domain = extract_domain(url)
    
    # Check for exact domain matches
    for prod_domain in PRODUCTIVE_DOMAINS:
        if prod_domain in domain:
            return {"productive": True, "confidence": 0.9, 
                    "reason": f"Domain '{domain}' is known for educational content"}
    
    # Special case for YouTube - check if it's shorts/reels or educational content
    if 'youtube.com' in domain:
        if any(term in url.lower() for term in ['/shorts', '/reels']):
            return {"productive": False, "confidence": 0.85, 
                    "reason": "Short-form video content tends to be distracting"}
        if any(term in url.lower() for term in ['/lecture', '/education', '/learn', '/course']):
            return {"productive": True, "confidence": 0.8, 
                    "reason": "Educational YouTube content"}
    
    for unprod_domain in UNPRODUCTIVE_DOMAINS:
        if unprod_domain in domain:
            return {"productive": False, "confidence": 0.85, 
                    "reason": f"Domain '{domain}' is generally entertainment-focused"}
    
    return None

def analyze_url_content(url):
    """Fetch and analyze content from the URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title and description
        title = soup.title.string if soup.title else ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'] if meta_desc else ""
        
        # Extract main text content (simplified)
        paragraphs = soup.find_all('p')
        content_text = ' '.join([p.text for p in paragraphs[:10]])  # First 10 paragraphs
        
        # Combine text for analysis
        full_text = f"{title} {description} {content_text}".lower()
        
        # Count educational and entertainment keywords
        edu_count = sum(1 for keyword in EDUCATIONAL_KEYWORDS if keyword in full_text)
        ent_count = sum(1 for keyword in ENTERTAINMENT_KEYWORDS if keyword in full_text)
        
        # Simple scoring without sentiment analysis
        if edu_count > ent_count and edu_count >= 3:
            return {"productive": True, "confidence": min(0.5 + (edu_count - ent_count) * 0.05, 0.9), 
                    "reason": f"Content contains educational keywords ({edu_count} found)"}
        elif ent_count > edu_count and ent_count >= 3:
            return {"productive": False, "confidence": min(0.5 + (ent_count - edu_count) * 0.05, 0.9), 
                    "reason": f"Content contains entertainment keywords ({ent_count} found)"}
        else:
            return {"productive": None, "confidence": 0.5, 
                    "reason": "Neutral content, could be either"}
            
    except Exception as e:
        return {"productive": None, "confidence": 0.3, 
                "reason": f"Failed to analyze content: {str(e)}"}

@app.route('/analyze', methods=['POST'])
def analyze_url():
    """API endpoint to analyze if a URL is productive for studying."""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({"error": "URL is required"}), 400
    
    url = data['url']
    
    # Validate URL format
    if not re.match(r'^https?://', url):
        return jsonify({"error": "Invalid URL format. URL must start with http:// or https://"}), 400
    
    # First check if domain is in our known lists
    domain_result = check_known_domains(url)
    
    if domain_result and domain_result["confidence"] > 0.7:
        return jsonify({
            "url": url,
            "is_productive": domain_result["productive"],
            "confidence": domain_result["confidence"],
            "reason": domain_result["reason"],
            "analysis_method": "domain-based"
        })
    
    # If not confident or domain not in lists, analyze content
    content_result = analyze_url_content(url)
    
    # Combine domain and content analysis if both available
    if domain_result and content_result and content_result["productive"] is not None:
        is_productive = domain_result["productive"] if domain_result["confidence"] > content_result["confidence"] else content_result["productive"]
        confidence = max(domain_result["confidence"], content_result["confidence"])
        reason = f"{domain_result['reason']} and {content_result['reason']}"
        analysis_method = "combined"
    elif content_result and content_result["productive"] is not None:
        is_productive = content_result["productive"]
        confidence = content_result["confidence"]
        reason = content_result["reason"]
        analysis_method = "content-based"
    elif domain_result:
        is_productive = domain_result["productive"]
        confidence = domain_result["confidence"]
        reason = domain_result["reason"]
        analysis_method = "domain-based"
    else:
        is_productive = None
        confidence = 0.4
        reason = "Insufficient information to determine productivity"
        analysis_method = "inconclusive"
    
    return jsonify({
        "url": url,
        "is_productive": is_productive,
        "confidence": confidence,
        "reason": reason,
        "analysis_method": analysis_method
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True, port=8080)

    #Example curl command for app route: curl -X POST http://localhost:8080/analyze -H "Content-Type: application/json" -d '{"url": "https://paint.toys/calligram/"}'