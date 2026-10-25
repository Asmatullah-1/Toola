from urllib.parse import quote_plus
import os

NEWS = """
# Labs & Models
OpenAI|https://openai.com/news/rss.xml
Google DeepMind|https://deepmind.google/blog/rss.xml
Google AI|https://blog.google/technology/ai/rss/
Google Research|https://research.google/blog/rss/
Anthropic (community feed)|https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml
Microsoft Research|https://www.microsoft.com/en-us/research/feed/
NVIDIA Blog|https://blogs.nvidia.com/feed/
NVIDIA Developer|https://developer.nvidia.com/blog/feed
AWS Machine Learning|https://aws.amazon.com/blogs/machine-learning/feed/
AWS What's New|https://aws.amazon.com/about-aws/whats-new/recent/feed/
Google Cloud|https://cloudblog.withgoogle.com/rss/
Hugging Face Blog|https://huggingface.co/blog/feed.xml
HF Daily Papers (community)|https://papers.takara.ai/api/feed
Apple ML Research|https://machinelearning.apple.com/rss.xml
Berkeley BAIR|https://bair.berkeley.edu/blog/feed.xml
CMU ML Blog|https://blog.ml.cmu.edu/feed/
The Gradient|https://thegradient.pub/rss/
Databricks|https://www.databricks.com/feed
Weights & Biases|https://wandb.ai/fully-connected/rss.xml
Replicate|https://replicate.com/blog/rss
LangChain|https://blog.langchain.dev/rss/
GitHub Blog|https://github.blog/feed/
GitHub Changelog|https://github.blog/changelog/feed/
Vercel|https://vercel.com/atom
Cloudflare|https://blog.cloudflare.com/rss/
Zapier|https://zapier.com/blog/feeds/latest/
JetBrains AI|https://blog.jetbrains.com/ai/feed/
Docker|https://www.docker.com/blog/feed/
Supabase|https://supabase.com/rss.xml
# News & Media
TechCrunch AI|https://techcrunch.com/category/artificial-intelligence/feed/
The Verge AI|https://www.theverge.com/rss/ai-artificial-intelligence/index.xml
VentureBeat AI|https://venturebeat.com/category/ai/feed/
Ars Technica|https://feeds.arstechnica.com/arstechnica/index
Wired AI|https://www.wired.com/feed/tag/ai/latest/rss
MIT Tech Review AI|https://www.technologyreview.com/topic/artificial-intelligence/feed
The Register AI|https://www.theregister.com/software/ai_ml/headlines.atom
ZDNet AI|https://www.zdnet.com/topic/artificial-intelligence/rss.xml
Engadget|https://www.engadget.com/rss.xml
9to5Google|https://9to5google.com/feed/
9to5Mac|https://9to5mac.com/feed/
MarkTechPost|https://www.marktechpost.com/feed/
Unite.AI|https://www.unite.ai/feed/
AI News|https://www.artificialintelligence-news.com/feed/
Analytics India Mag|https://analyticsindiamag.com/feed/
SiliconANGLE AI|https://siliconangle.com/category/ai/feed/
Techmeme|https://www.techmeme.com/feed.xml
The Decoder|https://the-decoder.com/feed/
Slashdot|http://rss.slashdot.org/Slashdot/slashdotMain
InfoQ AI/ML|https://feed.infoq.com/ai-ml-data-eng/
# Newsletters & Experts
Simon Willison|https://simonwillison.net/atom/everything/
AINews (smol.ai)|https://news.smol.ai/rss.xml
Latent Space|https://www.latent.space/feed
Import AI|https://importai.substack.com/feed
Ben's Bites|https://www.bensbites.com/feed
Interconnects|https://www.interconnects.ai/feed
Ahead of AI|https://magazine.sebastianraschka.com/feed
One Useful Thing|https://www.oneusefulthing.org/feed
Pragmatic Engineer|https://blog.pragmaticengineer.com/rss/
AI Snake Oil|https://www.aisnakeoil.com/feed
Last Week in AI|https://lastweekin.ai/feed
TLDR AI|https://tldr.tech/api/rss/ai
TLDR Tech|https://tldr.tech/api/rss/tech
Exponential View|https://www.exponentialview.co/feed
Platformer|https://www.platformer.news/rss/
Understanding AI|https://www.understandingai.org/feed
Zvi Mowshowitz|https://thezvi.substack.com/feed
Marcus on AI|https://garymarcus.substack.com/feed
Lilian Weng|https://lilianweng.github.io/index.xml
Chip Huyen|https://huyenchip.com/feed.xml
Eugene Yan|https://eugeneyan.com/rss/
Hamel Husain|https://hamel.dev/index.xml
Jay Alammar|https://jalammar.github.io/feed.xml
Andrej Karpathy|https://karpathy.github.io/feed.xml
Towards Data Science|https://towardsdatascience.com/feed
KDnuggets|https://www.kdnuggets.com/feed
Machine Learning Mastery|https://machinelearningmastery.com/blog/feed/
Analytics Vidhya|https://www.analyticsvidhya.com/feed/
DEV.to AI|https://dev.to/feed/tag/ai
Medium AI|https://medium.com/feed/tag/artificial-intelligence
Medium GenAI|https://medium.com/feed/tag/generative-ai
# Creative AI
r/midjourney|https://www.reddit.com/r/midjourney/new/.rss
r/aivideo|https://www.reddit.com/r/aivideo/new/.rss
r/comfyui|https://www.reddit.com/r/comfyui/new/.rss
r/SunoAI|https://www.reddit.com/r/SunoAI/new/.rss
r/runwayml|https://www.reddit.com/r/runwayml/new/.rss
# Tools & Launches
Product Hunt|https://www.producthunt.com/feed
Product Hunt AI|https://www.producthunt.com/feed?category=artificial-intelligence
BetaList|https://betalist.com/feed
HN Show|https://hnrss.org/show
HN Front Page|https://hnrss.org/frontpage
HN Best|https://hnrss.org/best
GitHub Trending (all)|https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml
GitHub Trending (Python)|https://mshibanami.github.io/GitHubTrendingRSS/daily/python.xml
Lobsters AI|https://lobste.rs/t/ai.rss
Lobsters|https://lobste.rs/rss
"""
PAPERS = {c: f"https://rss.arxiv.org/rss/cs.{c}" for c in ["AI", "CL", "LG", "CV", "HC", "SE", "IR"]}
AI_SUBS = ["LocalLLaMA", "MachineLearning", "artificial", "OpenAI", "ClaudeAI", "singularity", "ChatGPT",
           "StableDiffusion", "ollama", "ChatGPTPro", "PromptEngineering", "AI_Agents", "n8n", "automation", "GoogleGeminiAI"]
GNEWS = ["new AI model launch", "AI tool launch", "OpenAI", "Anthropic Claude", "Google Gemini", "Meta Llama",
         "Mistral AI", "DeepSeek", "Qwen Alibaba AI", "AI startup funding", "AI video generator", "AI image generator", "AI video editing tool", "AI writing tool"]
INDUSTRIES = """
Accounting|Accounting,tax
Banking|banking
Finance & Investing|FinancialCareers
Fintech|fintech
Insurance|Insurance
Mortgage & Lending|mortgagebrokers
Real Estate|realestate
Property Management|PropertyManagement
Facilities Management|facilitiesmanagement
Construction|Construction
Architecture|architecture
Civil Engineering|civilengineering
Mechanical Engineering|MechanicalEngineering
Electrical Engineering|ElectricalEngineering
Aerospace|aerospace
Software Development|ExperiencedDevs
DevOps & Cloud|devops
Cybersecurity|cybersecurity
IT & Sysadmin|sysadmin,ITManagers
Data Science|datascience
Data Analytics|analytics
Business Intelligence|BusinessIntelligence
Spreadsheets & Excel|excel
QA & Testing|QualityAssurance
Product Management|ProductManagement
UX & Product Design|UXDesign
Graphic Design|graphic_design
Technical Writing|technicalwriting
Marketing|marketing,digital_marketing
SEO|SEO
Social Media|socialmedia
Content Marketing|content_marketing
Copywriting|copywriting
Public Relations|publicrelations
Advertising & PPC|PPC,advertising
Sales|sales
SaaS|SaaS
CRM & Salesforce|salesforce
E-commerce|ecommerce,shopify
Retail|Retail
Restaurants|restaurateur
Food Service & Chefs|Chefit
Aviation|aviation
Logistics|logistics
Supply Chain|supplychain
Procurement|procurement
Warehousing|warehouse
Trucking|Truckers
Maritime & Shipping|maritime
Manufacturing|manufacturing
Lean & Six Sigma|sixsigma
Automotive|MechanicAdvice
Oil & Gas|oilandgasworkers
Solar & Renewables|solar
Electricians|electricians
HVAC|HVAC
Plumbing|Plumbing
Mining|mining
Agriculture|farming
Landscaping|landscaping
Telecom|telecom
Environmental Science|environmental_science
Lab Science|labrats
Biotech|biotech
Clinical Research|clinicalresearch
Health IT|healthIT
Medical Coding|medicalcoding
Nursing|nursing
Physicians|medicine
Pharmacy|pharmacy
Dentistry|Dentistry
Physical Therapy|physicaltherapy
Therapy & Counseling|therapists
Social Work|socialwork
Public Health|publichealth
Veterinary|veterinaryprofessionals
K-12 Teaching|Teachers
Early Childhood Education|ECEProfessionals
Higher Education|Professors
Academic Research|academia
Instructional Design|instructionaldesign
Libraries|librarians
Law Firms|LawFirm
Paralegals|paralegal
Legal Tech|LegalTech
Compliance|Compliance
Human Resources|humanresources
Recruiting|recruiting
Project Management|projectmanagement
Business Analysis|businessanalysis
Consulting|consulting
Customer Service|CustomerService
Customer Success|CustomerSuccess
Call Centers|callcenter
Executive Assistants|ExecutiveAssistants
Small Business|smallbusiness
Entrepreneurs|Entrepreneur
Freelancing|freelance
Nonprofit|nonprofit
Grant Writing|grantwriting
Government & Civil Service|civilservice
Urban Planning|urbanplanning
Journalism|Journalism
Writing & Publishing|writing
Translation|translator
Podcasting|podcasting
Video Production|videography
Photography|photography
Music Production|musicproduction
Game Development|gamedev
Animation & Film|animation
Fashion Design|fashiondesign
Interior Design|interiordesign
Event Planning|eventplanning
Weddings|WeddingPlanning
Personal Training|personaltraining
Video Editing|VideoEditing,premiere,davinciresolve
Motion Graphics|AfterEffects,MotionDesign
YouTube & Creators|NewTubers,PartneredYoutube
Streaming & Twitch|Twitch
Filmmaking|Filmmakers,cinematography
Screenwriting|Screenwriting
Audio Engineering|audioengineering
Voice Acting|VoiceActing
Photo Editing|photoshop,Lightroom
Illustration & Art|ArtistLounge
3D Art & Modeling|blender,3Dmodeling
UI Design|UI_Design
Web Design|web_design
Branding & Logo Design|logodesign
Print on Demand|PrintOnDemand
Presentation Design|powerpoint
Copy Editing|editors
Blogging|blogging
Self-Publishing|selfpublish
UX Writing|UXWriting
Newsletters & Substack|Substack
Publishing|publishing
Game Design|gamedesign
EDM & Beat Making|edmproduction
"""
SE = {"softwarerecs.stackexchange.com": "Software Recs", "workplace.stackexchange.com": "Workplace",
      "pm.stackexchange.com": "Project Mgmt", "webapps.stackexchange.com": "Web Apps", "writing.stackexchange.com": "Writing"}
SEARCH = ['"is there a tool"', '"how do I automate"', '"wasting hours"']


def news_sources():
    out, cat = [], "General"
    for line in NEWS.strip().splitlines():
        if line.startswith("#"):
            cat = line[1:].strip()
        elif "|" in line:
            n, u = line.split("|", 1)
            out.append((n, u, cat, "news"))
    out += [(f"arXiv cs.{c}", u, "Research", "paper") for c, u in PAPERS.items()]
    out += [(f"r/{s}", f"https://www.reddit.com/r/{s}/new/.rss", "Community", "news") for s in AI_SUBS]
    out += [(f"Google News: {q}", f"https://news.google.com/rss/search?q={quote_plus(q + ' when:1d')}&hl=en-US&gl=US&ceid=US:en", "News Search", "news") for q in GNEWS]
    return out


def pain_sources():
    out = []
    for line in INDUSTRIES.strip().splitlines():
        ind, subs = line.split("|")
        out += [(f"r/{x}", f"https://www.reddit.com/r/{x}/new/.rss", ind, "pain") for x in subs.split(",")]
    out += [(f"{n}", f"https://{d}/feeds", n, "pain") for d, n in SE.items()]
    out += [("Ask HN", "https://hnrss.org/ask", "Tech & Startups", "pain")]
    out += [(f"Reddit search {q}", f"https://www.reddit.com/search.rss?q={quote_plus(q)}&sort=new&t=week", "Reddit Search", "pain") for q in SEARCH]
    if os.path.exists("custom_feeds.txt"):
        for line in open("custom_feeds.txt", encoding="utf-8"):
            if "|" in line and not line.startswith("#"):
                n, u = line.strip().split("|", 1)
                out.append((n, u, "Quora / LinkedIn alerts", "pain"))
    return out


SECTORS = {
 "Creative & Media": "Graphic Design|UX & Product Design|Copywriting|Journalism|Writing & Publishing|Translation|Podcasting|Video Production|Photography|Music Production|Game Development|Animation & Film|Fashion Design|Interior Design|Technical Writing|Video Editing|Motion Graphics|YouTube & Creators|Streaming & Twitch|Filmmaking|Screenwriting|Audio Engineering|Voice Acting|Photo Editing|Illustration & Art|3D Art & Modeling|UI Design|Web Design|Branding & Logo Design|Print on Demand|Presentation Design|Copy Editing|Blogging|Self-Publishing|UX Writing|Newsletters & Substack|Publishing|Game Design|EDM & Beat Making|Social Media|Content Marketing",
 "Tech & Data": "Software Development|DevOps & Cloud|Cybersecurity|IT & Sysadmin|Data Science|Data Analytics|Business Intelligence|Spreadsheets & Excel|QA & Testing|Product Management|SaaS|CRM & Salesforce|Fintech|Telecom|Legal Tech|Health IT",
 "Health & Science": "Biotech|Clinical Research|Medical Coding|Nursing|Physicians|Pharmacy|Dentistry|Physical Therapy|Therapy & Counseling|Social Work|Public Health|Veterinary|Environmental Science|Lab Science",
 "Education & Public": "K-12 Teaching|Early Childhood Education|Higher Education|Academic Research|Instructional Design|Libraries|Nonprofit|Grant Writing|Government & Civil Service|Urban Planning",
 "Trades & Industry": "Construction|Architecture|Civil Engineering|Mechanical Engineering|Electrical Engineering|Aerospace|Facilities Management|Manufacturing|Lean & Six Sigma|Automotive|Oil & Gas|Solar & Renewables|Electricians|HVAC|Plumbing|Mining|Agriculture|Landscaping|Logistics|Supply Chain|Warehousing|Trucking|Maritime & Shipping|Aviation",
}
SECTOR_OF = {l.split("|")[0]: "Business & Professional" for l in INDUSTRIES.strip().splitlines()}
for _sec, _names in SECTORS.items():
    for _n in _names.split("|"):
        SECTOR_OF[_n] = _sec
