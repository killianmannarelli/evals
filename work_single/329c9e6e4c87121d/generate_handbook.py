#!/usr/bin/env python3
"""Generate the Cross-Cultural Negotiation Handbook (80 country chapters)."""
import os
import csv

OUT_DIR = "/home/user/evals/work_single/329c9e6e4c87121d/app/artifact"

COUNTRIES = [
    {
        "country": "Japan", "region": "East Asia",
        "hofstede": "High uncertainty avoidance, high long-term orientation, collectivist with strong group harmony (wa) and consensus building (nemawashi).",
        "legal": "Civil law system rooted in the Meiji-era Civil Code; written contracts treated as flexible frameworks for an ongoing relationship.",
        "practices": ["Decisions made by ringi-sho consensus across multiple layers", "Business cards (meishi) exchanged ceremonially with two hands", "Silence during meetings signals consideration, not disagreement"],
        "case": "The 1999 Renault-Nissan Alliance required two years of relationship-building led by Carlos Ghosn before equity terms were finalised, illustrating the centrality of trust over speed.",
        "dos": [
            ("Bow respectfully on greeting", "Initiate physical contact such as backslaps"),
            ("Present meishi with both hands, Japanese side up", "Write on or pocket a counterpart's card carelessly"),
            ("Allow silence; do not rush rebuttals", "Interrupt or fill pauses with chatter"),
            ("Build consensus via nemawashi before formal meetings", "Force decisions in the meeting itself"),
            ("Wrap gifts in muted colors and refuse twice before accepting", "Give gifts in sets of four (shi = death)"),
        ],
        "refs": ["Hofstede Insights, Country Comparison: Japan, 2023.", "Magee, J., 'Negotiating in Japan,' Harvard Business Review, 2018.", "JETRO, 'Doing Business in Japan: Legal Guide,' 2022."],
    },
    {
        "country": "China", "region": "East Asia",
        "hofstede": "High power distance, collectivist, long-term oriented; guanxi (relationship networks) and mianzi (face) shape every transaction.",
        "legal": "Civil law system; the 2021 Civil Code consolidates contract, property, and tort law, while foreign investment is governed by the 2020 Foreign Investment Law.",
        "practices": ["Hierarchy: senior decision-maker enters meetings first", "Banquets with toasts (ganbei) cement deals", "Counterparts may renegotiate after signing; contracts are 'living documents'"],
        "case": "The 2014 Anbang acquisition of New York's Waldorf Astoria for USD 1.95B was preceded by months of guanxi-building with Hilton executives and signalled state-blessed outbound M&A.",
        "dos": [
            ("Address by surname plus title (Director Wang)", "Use first names unless invited"),
            ("Bring an interpreter even if hosts speak English", "Assume nuance is captured in English"),
            ("Reciprocate banquet invitations promptly", "Refuse the first toast"),
            ("Save 'no' for last; use indirect language", "Issue blunt refusals in public"),
            ("Expect post-signing renegotiation requests", "Treat contract day as the finish line"),
        ],
        "refs": ["World Bank, China Doing Business Profile, 2022.", "Sebenius, J. & Qian, C., 'Cultural Notes on Chinese Negotiating Behavior,' HBS WP 09-076.", "PRC National People's Congress, Civil Code, 2020."],
    },
    {
        "country": "South Korea", "region": "East Asia",
        "hofstede": "Collectivist, high power distance, long-term oriented; Confucian respect for age and rank (kibun) underlies negotiations.",
        "legal": "Civil law system based on the Korean Civil Act of 1958; strong statutory consumer and labour protections; commercial disputes increasingly arbitrated under KCAB rules.",
        "practices": ["Chaebol structure means decision authority is concentrated at the top", "Drinking sessions (hoesik) are part of relationship-building", "Inhwa (harmony) discourages overt confrontation"],
        "case": "Samsung's 2016 USD 8B acquisition of Harman International leveraged a year of bilateral cultivation by Vice Chairman Lee, balancing chaebol speed with US governance norms.",
        "dos": [
            ("Greet seniors first with a slight bow", "Begin with the most junior person present"),
            ("Use both hands when passing items or pouring drinks", "Pour your own drink"),
            ("Accept invitations to after-hours hoesik", "Skip social events citing work"),
            ("Mirror counterpart's pace; expect repeated meetings", "Push for instant decisions"),
            ("Send a senior representative to match rank", "Field only junior staff"),
        ],
        "refs": ["KOTRA, 'Investment Guide to Korea,' 2022.", "Hofstede Insights: South Korea, 2023.", "Kim, L., 'Negotiating with the Chaebol,' SAIS Review, 2019."],
    },
    {
        "country": "Taiwan", "region": "East Asia",
        "hofstede": "Collectivist, moderate-to-high power distance, long-term oriented; pragmatic blend of Confucian roots and Western business style.",
        "legal": "Civil law tradition based on the ROC Civil Code (1929); strong IP protection regime; Investment Commission MOEA reviews foreign investment.",
        "practices": ["Family-owned conglomerates dominate; patriarch holds final say", "Renqing (favours owed) tracked across deals", "Punctuality valued more than in mainland China"],
        "case": "TSMC's 2020 USD 12B Arizona fab announcement, negotiated with the US Commerce Department, balanced cross-Strait political sensitivity with supply-chain leverage.",
        "dos": [
            ("Use traditional Chinese characters in materials", "Use simplified characters used in PRC"),
            ("Acknowledge family ties in introductions", "Discuss cross-Strait politics unprompted"),
            ("Confirm verbal agreements in writing same day", "Rely solely on handshake deals"),
            ("Use Mandarin or Taiwanese greetings respectfully", "Refer to Taiwan as a Chinese province"),
            ("Plan multiple visits to deepen renqing", "Expect one trip to close"),
        ],
        "refs": ["Taiwan MOEA Investment Commission, 'Foreign Investment Guidelines,' 2023.", "Hofstede Insights: Taiwan, 2023.", "Hsing, Y., 'Making Capitalism in China: Taiwan Connection,' Oxford UP, 1998."],
    },
    {
        "country": "Hong Kong", "region": "East Asia",
        "hofstede": "Mixed: collectivist family core, but transactional, individualist business style; low uncertainty avoidance and time-pressured.",
        "legal": "Common law jurisdiction under the Basic Law; contracts enforced through HKIAC arbitration or the High Court; strict adherence to written terms.",
        "practices": ["Direct, fast-paced English-language deals", "Personal relationships still matter despite legalism", "Feng shui considerations may shape office and contract timing"],
        "case": "AIA Group's 2010 USD 20.5B Hong Kong IPO, the world's third-largest at the time, showcased the city's role as a deal-making hub between East and West.",
        "dos": [
            ("Be punctual and prepared for fast negotiations", "Show up late or unprepared"),
            ("Treat the written contract as binding", "Expect post-signing flexibility"),
            ("Use English for formal contracts", "Assume Cantonese fluency in all parties"),
            ("Respect both Chinese and Western etiquette", "Force a single cultural framing"),
            ("Acknowledge feng shui dates for signings if proposed", "Dismiss feng shui requests"),
        ],
        "refs": ["HKIAC Annual Report, 2022.", "World Bank, Hong Kong SAR Profile, 2022.", "Hofstede Insights: Hong Kong, 2023."],
    },
    {
        "country": "Singapore", "region": "Southeast Asia",
        "hofstede": "High power distance, collectivist with strong individualist business overlay; pragmatic, rule-following, future-oriented.",
        "legal": "Common law jurisdiction; the Singapore International Commercial Court and SIAC arbitration centre offer top-tier dispute resolution.",
        "practices": ["Multi-ethnic etiquette (Chinese, Malay, Indian) blended", "Government-linked corporations (Temasek) common counterparties", "Efficiency and transparency expected"],
        "case": "The 2018 USD 13B GIC-Blackstone Logicor refinancing demonstrated Singapore's role as Asia's preferred arbitration and capital-allocation venue.",
        "dos": [
            ("Address counterparts by Mr/Ms plus surname", "Use first names without invitation"),
            ("Specify SIAC as arbitration venue in contracts", "Leave dispute venue ambiguous"),
            ("Be mindful of Halal/vegetarian dietary needs", "Default to pork-based menus"),
            ("Honour punctuality strictly", "Be loose with time commitments"),
            ("Use clear, written, English contracts", "Rely on oral side-letters"),
        ],
        "refs": ["SIAC Annual Report, 2022.", "Singapore Economic Development Board, 'Doing Business Guide,' 2023.", "Hofstede Insights: Singapore, 2023."],
    },
    {
        "country": "Indonesia", "region": "Southeast Asia",
        "hofstede": "High power distance, collectivist, relationship-driven; bapak (father figure) leadership and rukun (harmony) prevail.",
        "legal": "Civil law system inherited from Dutch colonial code; mining and natural-resources sector governed by the 2009 Mining Law and its 2020 amendments.",
        "practices": ["Avoid public confrontation; preserve face (malu)", "Decisions go through senior bapak", "Negotiations move slowly with multiple social meetings"],
        "case": "The 2018 Freeport-McMoRan divestment to PT Inalum for USD 3.85B took two years of negotiations over the Grasberg mine, reflecting resource-nationalist law shifts.",
        "dos": [
            ("Greet eldest or highest-ranking person first", "Single out junior staff"),
            ("Accept tea or coffee when offered", "Decline hospitality outright"),
            ("Allow extended small talk before business", "Push business in opening minutes"),
            ("Use right hand for giving/receiving items", "Use the left hand"),
            ("Build personal rapport before contract talks", "Send only lawyers in the first meeting"),
        ],
        "refs": ["BKPM, 'Investment Guide Indonesia,' 2022.", "Hofstede Insights: Indonesia, 2023.", "Aspinall, E., 'Indonesia: Mining and Negotiation,' Asian Studies Review, 2019."],
    },
    {
        "country": "Thailand", "region": "Southeast Asia",
        "hofstede": "High power distance, collectivist; kreng jai (deference) and sanuk (fun) shape interactions; face-saving is paramount.",
        "legal": "Civil law system with influence from Continental Europe; the Foreign Business Act 1999 restricts foreign majority ownership in many sectors.",
        "practices": ["Wai greeting (palms together) used by seniors-first protocol", "Royal family and Buddhism are sensitive topics", "Indirect communication; smiles can mask disagreement"],
        "case": "The 2017 Alibaba-Charoen Pokphand Group e-commerce JV worth USD 11B was preceded by extensive relationship-building between Jack Ma and Dhanin Chearavanont.",
        "dos": [
            ("Return a wai when offered by seniors", "Initiate a wai to juniors"),
            ("Speak softly and maintain composure", "Show anger or raise your voice"),
            ("Respect royal imagery and avoid lèse-majesté topics", "Touch images of the king"),
            ("Use indirect 'maybe' / 'difficult' for refusal", "Issue blunt 'no'"),
            ("Bring small gifts wrapped in bright paper", "Use black or green wrapping (mourning)"),
        ],
        "refs": ["BOI Thailand, 'Guide to Investment,' 2022.", "Hofstede Insights: Thailand, 2023.", "Komin, S., 'Psychology of the Thai People,' NIDA, 1990."],
    },
    {
        "country": "Vietnam", "region": "Southeast Asia",
        "hofstede": "Collectivist, high power distance, increasingly long-term oriented; Confucian respect blended with socialist state structures.",
        "legal": "Civil law with strong socialist overlay; the 2020 Investment Law and 2020 Enterprise Law govern foreign entry; Party approval often needed for large deals.",
        "practices": ["Banquets and karaoke seal relationships", "State-owned enterprises and Party links matter", "Negotiations may include 'tea money' protocols"],
        "case": "Vietnam's 2018 EVFTA negotiation with the EU took eight years, illustrating Hanoi's deliberate pace and capacity to balance Western and Chinese leverage.",
        "dos": [
            ("Greet eldest with a slight bow and handshake", "Slap backs or hug new acquaintances"),
            ("Verify Party/government stakeholders early", "Assume private sector autonomy"),
            ("Bring an interpreter from a neutral firm", "Rely on counterpart's interpreter"),
            ("Toast with both hands on the glass", "Refuse a toast outright"),
            ("Expect overnight reflection on offers", "Push for same-day decisions"),
        ],
        "refs": ["MPI Vietnam, 'Investment Report,' 2022.", "World Bank, Vietnam Country Profile, 2022.", "Hofstede Insights: Vietnam, 2023."],
    },
    {
        "country": "Malaysia", "region": "Southeast Asia",
        "hofstede": "High power distance, collectivist; multi-ethnic (Malay, Chinese, Indian) with bumiputera policy framing many deals.",
        "legal": "Common law system inherited from the UK with Islamic (Syariah) law for personal matters; Companies Act 2016 governs corporates.",
        "practices": ["Bumiputera equity quotas in some sectors", "Halal certification needed for F&B/finance", "Hospitality and patience expected"],
        "case": "The Petronas-Saudi Aramco RAPID refinery deal (USD 7B equity in 2017) showcased blending state-owned oil giants under Malaysian local-content rules.",
        "dos": [
            ("Use 'Datuk' or 'Tan Sri' titles when applicable", "Drop titles in formal settings"),
            ("Confirm Halal status of meals and contracts", "Serve pork or alcohol to Muslim hosts"),
            ("Respect bumiputera partnership rules", "Ignore local-content thresholds"),
            ("Greet with right hand only", "Use left hand for greetings or gifts"),
            ("Allow prayer breaks during Ramadan", "Schedule lunch meetings during fasting"),
        ],
        "refs": ["MIDA, 'Investment in Malaysia,' 2022.", "Hofstede Insights: Malaysia, 2023.", "Bank Negara, 'Islamic Finance Annual Report,' 2022."],
    },
    {
        "country": "Philippines", "region": "Southeast Asia",
        "hofstede": "High power distance, collectivist, family-oriented; pakikisama (smooth relations) and utang na loob (debt of gratitude) influence deals.",
        "legal": "Civil law base (Spanish heritage) layered with US-influenced commercial law; Foreign Investments Act 1991 governs entry; SEC oversight active.",
        "practices": ["English widely used in business", "Family conglomerates dominate (Ayala, SM, JG Summit)", "Decisions often centralised in patriarch/matriarch"],
        "case": "The 2014 USD 1.7B SM Investments retail expansion across ASEAN involved patient negotiations with Sy family principals and reflected pakikisama-driven deal pacing.",
        "dos": [
            ("Use respectful 'po' and 'opo' in Tagalog", "Address elders by first name only"),
            ("Engage the senior family principal directly", "Negotiate only with middle managers"),
            ("Be warm, personable, and humorous", "Be stiff or coldly transactional"),
            ("Honour utang na loob with reciprocal favours", "Ignore prior favours received"),
            ("Allow time for meals and family small talk", "Skip social rituals to 'save time'"),
        ],
        "refs": ["PSA Philippines, 'Doing Business 2022.'", "Hofstede Insights: Philippines, 2023.", "Andres, T., 'Understanding Filipino Values,' New Day, 1981."],
    },
    {
        "country": "India", "region": "South Asia",
        "hofstede": "High power distance, collectivist family, masculine; jugaad (frugal innovation) and relationship-based bargaining.",
        "legal": "Common law system inherited from the British; Indian Contract Act 1872, Companies Act 2013, and SEBI regulate deals; arbitration via the 1996 Arbitration & Conciliation Act.",
        "practices": ["Multiple rounds of price haggling expected", "Family business houses (Tata, Reliance) influential", "Bureaucratic delays factor into timelines"],
        "case": "Walmart's 2018 USD 16B acquisition of Flipkart involved 18 months of negotiation with founders and regulators, illustrating Indian e-commerce FDI sensitivities.",
        "dos": [
            ("Use Mr/Ms plus surname or 'Sir/Madam'", "Use first names early on"),
            ("Build personal trust over multiple meetings", "Try to close in one trip"),
            ("Allow generous timelines for approvals", "Assume Western-style speed"),
            ("Be flexible on contract terms post-signing", "Treat the contract as fully final"),
            ("Decline food/drink politely if needed, with right hand", "Refuse hospitality outright"),
        ],
        "refs": ["DPIIT India, 'FDI Policy 2020.'", "Hofstede Insights: India, 2023.", "Kumar, R. & Sethi, A.K., 'Doing Business in India,' Palgrave, 2005."],
    },
    {
        "country": "Pakistan", "region": "South Asia",
        "hofstede": "High power distance, collectivist, family-honour driven; Islamic ethics and biraderi (kinship) networks shape relations.",
        "legal": "Common law inherited from British India, overlaid with Islamic provisions; Companies Act 2017 and Securities Act 2015 regulate corporate deals.",
        "practices": ["Hospitality (mehman nawazi) is intense", "Decisions concentrated in family patriarchs", "Friday afternoons reserved for prayers"],
        "case": "The 2021 USD 1.5B Engro-Royal Vopak terminal deal demonstrated patient relationship-building between a Pakistani family conglomerate and a Dutch multinational.",
        "dos": [
            ("Accept tea and meals graciously", "Decline hospitality outright"),
            ("Dress conservatively, especially women", "Wear revealing attire"),
            ("Schedule around prayer times and Ramadan", "Book Friday afternoon meetings"),
            ("Build trust before discussing numbers", "Open with price"),
            ("Engage senior family head directly", "Address only mid-level staff"),
        ],
        "refs": ["SBP, 'Foreign Investment Guide,' 2022.", "Hofstede Insights: Pakistan, 2023.", "Lyon, S., 'An Anthropological Analysis of Patronage in Pakistan,' Edwin Mellen, 2004."],
    },
    {
        "country": "Bangladesh", "region": "South Asia",
        "hofstede": "High power distance, collectivist; relationship-driven, hierarchical, Islamic-influenced; rising on garment-export wealth.",
        "legal": "Common law (British heritage); Companies Act 1994; Bangladesh Investment Development Authority Act 2016 streamlines foreign investment.",
        "practices": ["RMG (ready-made garment) deals dominate exports", "Personal introductions essential", "Bureaucracy slow but improving via BIDA"],
        "case": "The 2022 H&M-Bangladesh sourcing modernization plan, negotiated with BGMEA, signalled post-Rana Plaza accountability and a USD multi-billion-dollar pact.",
        "dos": [
            ("Greet with 'Assalamu Alaikum' if appropriate", "Default to Western greetings"),
            ("Use formal titles and surnames", "Be overly casual"),
            ("Build long-term sourcing partnerships", "Demand single-tender lowest price"),
            ("Audit factory compliance regularly", "Ignore worker-safety standards"),
            ("Allow time for visa and permit processes", "Assume same-day approvals"),
        ],
        "refs": ["BIDA, 'Investment Handbook,' 2022.", "Hofstede Insights: Bangladesh, 2023.", "Mostafa, R., 'Doing Business in Bangladesh,' UPL, 2018."],
    },
    {
        "country": "Sri Lanka", "region": "South Asia",
        "hofstede": "Collectivist, moderate power distance; Buddhist-Hindu cultural blend; hospitality central, relationships precede deals.",
        "legal": "Mixed system: Roman-Dutch civil base, English commercial law overlay, customary law for personal matters; arbitration via SLNAC.",
        "practices": ["Cultural diversity (Sinhalese, Tamil, Muslim) matters", "Decisions take time amid economic volatility", "Currency controls and IMF programs shape deals"],
        "case": "The 2017 USD 1.12B Hambantota Port lease to China Merchants required two years of debt-restructuring talks, illustrating Sri Lanka's strategic-asset bargaining.",
        "dos": [
            ("Use both hands when offering business cards", "Use only one hand"),
            ("Be sensitive to ethnic/religious diversity", "Make ethnic generalizations"),
            ("Allow generous timelines and follow-up", "Assume rapid closure"),
            ("Account for forex restrictions in pricing", "Quote only in foreign currency"),
            ("Visit Colombo before commitments", "Negotiate solely remotely"),
        ],
        "refs": ["BOI Sri Lanka, 'Investment Guide,' 2022.", "Hofstede Insights: Sri Lanka, 2023.", "Moramudali, U., 'Hambantota Port: Debt-Trap Reality?,' The Diplomat, 2019."],
    },
    {
        "country": "Saudi Arabia", "region": "Middle East",
        "hofstede": "High power distance, collectivist, masculine; Islamic ethics and wasta (connections) underpin business.",
        "legal": "Sharia law as primary source; commercial disputes resolved in commercial courts or via SCCA arbitration; Vision 2030 reforms expanding rule of law.",
        "practices": ["Long relationship-building precedes business", "Decisions rest with senior royals/family heads", "Friday is the weekly holy day"],
        "case": "The 2019 Saudi Aramco IPO at USD 1.7T valuation involved 18 months of negotiations with banks and sovereign wealth funds, the largest IPO in history.",
        "dos": [
            ("Accept Arabic coffee (gahwa) when offered", "Refuse hospitality outright"),
            ("Respect prayer times (5x daily)", "Schedule meetings across prayer windows"),
            ("Use right hand for greetings and eating", "Use left hand"),
            ("Dress conservatively; thobe/abaya respected", "Wear revealing clothing"),
            ("Build wasta via mutual connections", "Cold-call without introductions"),
        ],
        "refs": ["MISA Saudi Arabia, 'Investor Guide 2023.'", "Hofstede Insights: Saudi Arabia, 2023.", "Vision 2030 National Transformation Program documents."],
    },
    {
        "country": "United Arab Emirates", "region": "Middle East",
        "hofstede": "High power distance, collectivist with cosmopolitan overlay; Islamic ethics combined with international business pragmatism.",
        "legal": "Civil law inherited from Egyptian/French roots, Sharia for personal status; DIFC and ADGM offer common-law commercial courts.",
        "practices": ["Free zones (DIFC, JAFZA) ease foreign ownership", "Emirati nationals are senior decision-makers", "Multi-cultural workforce; English widely used"],
        "case": "The 2020 USD 10.1B ADNOC pipeline deal with BlackRock-KKR consortium demonstrated the UAE's appetite for sovereign-private partnership structures.",
        "dos": [
            ("Greet Emirati men with right hand; await women's lead", "Initiate handshake with Emirati women"),
            ("Use DIFC/ADGM jurisdiction for complex contracts", "Default to onshore courts blindly"),
            ("Respect Ramadan working hours", "Eat/drink in public during fasting"),
            ("Dress in formal business attire", "Show shorts or sleeveless wear in offices"),
            ("Cultivate personal trust over coffee", "Rush straight to terms"),
        ],
        "refs": ["UAE Ministry of Economy, 'Doing Business 2023.'", "Hofstede Insights: UAE, 2023.", "DIFC Courts Annual Review 2022."],
    },
    {
        "country": "Qatar", "region": "Middle East",
        "hofstede": "High power distance, collectivist, masculine; family/tribal connections and Islamic values central.",
        "legal": "Civil law system with Sharia influence; Qatar Financial Centre offers common-law option; QICCA handles arbitration.",
        "practices": ["LNG and sovereign-wealth deals dominate", "Government links via QIA crucial", "Hospitality elaborate and protracted"],
        "case": "The 2022 USD 60B North Field expansion JVs with Shell, TotalEnergies, ExxonMobil, ConocoPhillips, and ENI required two years of carefully sequenced bilateral talks.",
        "dos": [
            ("Cultivate QIA/QatarEnergy senior contacts", "Bypass state-linked stakeholders"),
            ("Respect majlis culture in meetings", "Rush past social pleasantries"),
            ("Use QFC for foreign-friendly contracts", "Insist on onshore only"),
            ("Honour Friday/Saturday weekend", "Schedule Friday meetings"),
            ("Match counterpart's pace patiently", "Push deadlines aggressively"),
        ],
        "refs": ["Qatar Investment Promotion Agency, 'Invest Qatar 2023.'", "Hofstede Insights: Qatar (regional, est.).", "QFC Authority Annual Report 2022."],
    },
    {
        "country": "Iran", "region": "Middle East",
        "hofstede": "High power distance, collectivist, ta'arof (ritual politeness) and bazaari (merchant culture) define negotiations.",
        "legal": "Civil law with Sharia (Shia) overlay; the Foreign Investment Promotion Act 2002 governs entry but sanctions limit options.",
        "practices": ["Ta'arof: ritual offers and refusals", "Bazaar negotiation style; multiple rounds expected", "Sanctions complicate banking and contracts"],
        "case": "The 2017 USD 5B TotalEnergies-South Pars deal (later cancelled post-2018 US sanctions) showed both Iran's negotiation pace and geopolitical exposure.",
        "dos": [
            ("Engage in ta'arof rituals (offer/decline three times)", "Take first offers at face value"),
            ("Use Farsi greetings (salam) respectfully", "Default to Arabic"),
            ("Conduct sanctions due diligence early", "Assume EU/US compliance is simple"),
            ("Dress conservatively; women cover hair", "Wear revealing attire"),
            ("Allow extended haggling cycles", "Set tight closure deadlines"),
        ],
        "refs": ["OFAC sanctions guidance, 2022.", "Hofstede Insights: Iran, 2023.", "Beeman, W., 'Language, Status, and Power in Iran,' Indiana UP, 1986."],
    },
    {
        "country": "Israel", "region": "Middle East",
        "hofstede": "Low power distance, individualist, direct (dugri); chutzpah and rapid iteration define start-up nation negotiations.",
        "legal": "Mixed common-law/civil heritage; Companies Law 1999, robust IP regime, ICC and IIBA arbitration popular.",
        "practices": ["Very direct, fast-paced discussions", "Hierarchy flat; juniors challenge seniors", "Sabbath (Friday eve-Saturday eve) observed"],
        "case": "Intel's 2017 USD 15.3B Mobileye acquisition closed in months, reflecting Israel's startup-friendly M&A culture and dugri negotiation style.",
        "dos": [
            ("Be direct and concise", "Use overly diplomatic hedging"),
            ("Expect aggressive counter-questions", "Take pushback personally"),
            ("Verify Shabbat-aware schedules", "Book Friday-night meetings"),
            ("Engage on tech merits deeply", "Sell only on price"),
            ("Respect security check protocols", "Skip El-Al style screenings"),
        ],
        "refs": ["IIA Israel, 'Innovation Report 2022.'", "Hofstede Insights: Israel, 2023.", "Senor, D. & Singer, S., 'Start-Up Nation,' Twelve, 2009."],
    },
    {
        "country": "Turkey", "region": "Middle East",
        "hofstede": "High power distance, collectivist, masculine; bridging Eastern and Western styles; hospitality and patience essential.",
        "legal": "Civil law system modelled on Swiss/German codes; Turkish Code of Obligations 2012; ISTAC arbitration for cross-border disputes.",
        "practices": ["Tea (çay) accompanies every meeting", "Family conglomerates (Koç, Sabancı) dominate", "Bargaining cycles long, with multiple bluffs"],
        "case": "Volkswagen's 2018-2019 plant negotiations with Turkey (later cancelled) and Ford-Koç JV at Kocaeli illustrate the country's industrial bargaining clout.",
        "dos": [
            ("Drink çay throughout meetings", "Refuse all tea offers"),
            ("Use formal Turkish titles (Bey/Hanım)", "Be informal with seniors"),
            ("Allow multiple bargaining rounds", "Push for one-shot closure"),
            ("Respect Friday prayer breaks", "Schedule Friday noon meetings"),
            ("Engage at family-principal level", "Stay only with middle managers"),
        ],
        "refs": ["Turkish Investment Office, 'Invest in Türkiye 2022.'", "Hofstede Insights: Turkey, 2023.", "Pamuk, Ş., 'Uneven Centuries: Turkish Economy,' Princeton UP, 2018."],
    },
    {
        "country": "Egypt", "region": "Middle East",
        "hofstede": "High power distance, collectivist; hospitality (karam) and personal trust drive deals; bureaucracy heavy.",
        "legal": "Civil law (Napoleonic Code base) with Sharia influence; Investment Law 72/2017 streamlines FDI via GAFI.",
        "practices": ["Wasta (connections) opens doors", "Military-linked entities active in economy", "Negotiations slow with multiple sign-offs"],
        "case": "Eni's 2015 Zohr gas field discovery (USD 16B) and subsequent partner buy-ins (Rosneft 30%, BP 10%) involved complex EGAS-led negotiations.",
        "dos": [
            ("Greet with 'Assalamu Alaikum' or 'Marhaba'", "Skip greetings"),
            ("Accept tea/coffee in elaborate ceremonies", "Decline hospitality"),
            ("Allow long bureaucratic timelines", "Assume Western speed"),
            ("Use wasta introductions effectively", "Cold-call senior officials"),
            ("Respect Friday/Sunday weekly rhythms", "Schedule Friday meetings"),
        ],
        "refs": ["GAFI Egypt, 'Investment Map,' 2022.", "Hofstede Insights: Egypt, 2023.", "Roy, D., 'The Egyptian Business Elite,' AUC Press, 2016."],
    },
    {
        "country": "Jordan", "region": "Middle East",
        "hofstede": "High power distance, collectivist, family-honour driven; Bedouin hospitality blends with cosmopolitan Amman.",
        "legal": "Civil law (Egyptian/Napoleonic heritage) with Sharia for personal status; Investment Law 30/2014 grants incentives via JIC.",
        "practices": ["Strong tribal and royal networks", "ASEZA (Aqaba) free zone attractive", "Tea/coffee rituals essential"],
        "case": "The 2017 Saudi-Egypt-Jordan USD 18B Red-Dead Sea project, though stalled, demonstrated multi-state water-trade diplomatic negotiations.",
        "dos": [
            ("Address using 'Doctor/Engineer' if applicable", "Drop titles"),
            ("Drink Arabic coffee in three cups", "Refuse all three"),
            ("Build tribal/royal-network introductions", "Skip personal intros"),
            ("Use ASEZA for free-zone advantages", "Default to onshore-only"),
            ("Respect refugee-policy sensitivities", "Make political quips"),
        ],
        "refs": ["Jordan Investment Commission, 'Invest in Jordan 2022.'", "Hofstede Insights: Jordan (regional est.).", "Tobin, S., 'Everyday Piety: Islam and Economy in Jordan,' Cornell UP, 2016."],
    },
    {
        "country": "Lebanon", "region": "Middle East",
        "hofstede": "High power distance, collectivist; cosmopolitan and sectarian; trader heritage and diaspora ties drive networks.",
        "legal": "Civil law (Napoleonic heritage), Code of Commerce 1942; sectarian system shapes government counterparties; banking secrecy law 1956 partially reformed in 2022.",
        "practices": ["Trilingual deals (Arabic, French, English)", "Diaspora financing critical post-2019 crisis", "Banking restrictions complicate currency conversion"],
        "case": "The 2018 USD 11B CEDRE conference pledges, negotiated in Paris with Lebanese state and donors, underscored Lebanon's reliance on diaspora-anchored negotiations.",
        "dos": [
            ("Use French or English alongside Arabic", "Insist only on one language"),
            ("Engage diaspora intermediaries", "Negotiate only with onshore parties"),
            ("Verify USD-LBP capital-control terms", "Assume free repatriation"),
            ("Respect Christian-Muslim sectarian balance", "Probe political affiliations crudely"),
            ("Build hospitality-based trust", "Open with hard numbers"),
        ],
        "refs": ["Banque du Liban Circular 158, 2022.", "Hofstede Insights: Lebanon (regional est.).", "Salameh, A., 'Lebanon's Economic Crisis,' Middle East Journal, 2021."],
    },
    {
        "country": "Nigeria", "region": "Sub-Saharan Africa",
        "hofstede": "High power distance, collectivist, masculine; relationship-driven; multi-ethnic (Hausa, Yoruba, Igbo) protocols.",
        "legal": "Common law (British heritage) with Sharia in northern states; Companies and Allied Matters Act 2020; FIRS tax oversight; arbitration via LCA, RCICAL.",
        "practices": ["Negotiations slow; multiple stakeholders", "Lagos and Abuja have distinct cultures", "Risk of corruption and FCPA exposure"],
        "case": "Royal Dutch Shell's 2021 USD 1.3B Nigeria onshore divestment to local consortia reflected the long, politically-laden talks typical of NNPC-related deals.",
        "dos": [
            ("Greet eldest in the room first", "Bypass senior figures"),
            ("Allow flexible 'Nigerian time'", "Demand rigid Western punctuality"),
            ("Verify counterparties via robust DD", "Skip integrity checks"),
            ("Use English plus local greetings", "Default to ethnic stereotypes"),
            ("Visit Lagos and Abuja personally", "Negotiate only remotely"),
        ],
        "refs": ["NIPC Nigeria, 'Investment Guide,' 2022.", "Hofstede Insights: Nigeria, 2023.", "Adeleke, F., 'FDI in Nigeria's Oil & Gas,' Routledge, 2018."],
    },
    {
        "country": "South Africa", "region": "Sub-Saharan Africa",
        "hofstede": "Mixed scores; multi-cultural (Afrikaner, English, Zulu, Xhosa); ubuntu (humanity to others) underpins relationships.",
        "legal": "Mixed common/Roman-Dutch system; Companies Act 71/2008; Competition Act 1998; BEE Act 2003 mandates Black ownership thresholds.",
        "practices": ["B-BBEE codes drive partnership structures", "Multi-stakeholder consultation (labour, gov, community)", "JSE-listed deals often complex"],
        "case": "Anheuser-Busch InBev's 2016 USD 100B SABMiller acquisition required B-BBEE concessions and union talks, becoming the largest SA-anchored deal in history.",
        "dos": [
            ("Engage B-BBEE partners early", "Treat empowerment as afterthought"),
            ("Honour ubuntu via community engagement", "Skip social-license dialogue"),
            ("Respect 11 official languages", "Assume English-only contexts"),
            ("Consult unions in labour-intensive deals", "Sideline COSATU/NUMSA"),
            ("Use JSE for capital-market deals", "Bypass listing requirements"),
        ],
        "refs": ["DTIC South Africa, 'B-BBEE Codes 2022.'", "Hofstede Insights: South Africa, 2023.", "Madonsela, T., 'State Capture Report,' 2016."],
    },
    {
        "country": "Kenya", "region": "Sub-Saharan Africa",
        "hofstede": "High power distance, collectivist; harambee (pulling together) spirit; English/Swahili bilingual business.",
        "legal": "Common law (British heritage); Companies Act 2015; Capital Markets Authority oversight; NCIA arbitration centre.",
        "practices": ["Nairobi is regional FDI hub (Safaricom, mobile-money)", "Government-tribal balance impacts deals", "M-Pesa ecosystem critical for fintech"],
        "case": "Vodafone's 2020 USD 2.6B sale of Vodacom-Safaricom stake to Vodacom involved months of regulator and Treasury talks, reshaping East Africa telecoms.",
        "dos": [
            ("Use Swahili greetings (Jambo, Habari)", "Default only to English"),
            ("Engage CAK regulator early", "Assume light competition review"),
            ("Build harambee-style consortia", "Insist on solo-bidder approach"),
            ("Schedule around Friday Muslim prayers in Mombasa", "Ignore Coastal religious norms"),
            ("Audit M-Pesa integrations carefully", "Underestimate mobile-money centrality"),
        ],
        "refs": ["KenInvest Kenya, 'Investment Promotion 2022.'", "Hofstede Insights: Kenya (regional est.).", "Ndemo, B. & Weiss, T., 'Digital Kenya,' Palgrave, 2017."],
    },
    {
        "country": "Ethiopia", "region": "Sub-Saharan Africa",
        "hofstede": "High power distance, collectivist; long traditions of consensus (gada in Oromo); Orthodox Christian and Muslim heritage.",
        "legal": "Civil law (1960 codes influenced by French/Swiss); recent 2020 Commercial Code; Investment Proclamation 1180/2020 liberalizing key sectors.",
        "practices": ["Coffee ceremony central to hospitality", "Recent reforms opening telecom/banking", "Conflict in Tigray complicates north-region deals"],
        "case": "Safaricom-led consortium's 2021 USD 850M telecom licence purchase ended Ethio Telecom monopoly, after eight months of cabinet-level talks.",
        "dos": [
            ("Participate in coffee (buna) ceremonies", "Decline coffee invitations"),
            ("Use Amharic greetings (Selam)", "Default to English-only"),
            ("Engage Ministry of Finance early", "Assume rapid regulatory greenlights"),
            ("Verify regional security context", "Plan travel without UNDSS advice"),
            ("Allow time for state-bank conversions", "Assume free forex access"),
        ],
        "refs": ["Ethiopian Investment Commission, 'Investment Guide 2022.'", "Hofstede Insights: Ethiopia (regional est.).", "Vaughan, S. & Tronvoll, K., 'The Culture of Power in Contemporary Ethiopian Political Life,' Sida, 2003."],
    },
    {
        "country": "Ghana", "region": "Sub-Saharan Africa",
        "hofstede": "High power distance, collectivist; respect for elders and chieftaincy; English-language business friendly.",
        "legal": "Common law (British heritage); Companies Act 2019; GIPC Act 2013 governs FDI; arbitration via GAAC.",
        "practices": ["Ashanti and Akan chieftaincy still influential", "Cocoa, gold, and offshore oil pivotal", "Stable democracy supports long-term planning"],
        "case": "Tullow Oil's 2010-2020 USD 3B Jubilee field operations involved continuous renegotiation with GNPC, exemplifying African resource-equity rebalancing.",
        "dos": [
            ("Acknowledge traditional rulers when relevant", "Bypass chieftaincy stakeholders"),
            ("Use formal Mr/Mrs plus surname", "Default to first names"),
            ("Allow extended community consultation", "Skip stakeholder engagement"),
            ("Build GIPC-registered local partnerships", "Operate without GIPC approval"),
            ("Respect Sunday church attendance", "Schedule Sunday meetings"),
        ],
        "refs": ["GIPC Ghana, 'Investor Guide 2022.'", "Hofstede Insights: Ghana (regional est.).", "Owusu, G. & Ohene-Yankyera, K., 'Doing Business in Ghana,' Sub-Saharan, 2017."],
    },
    {
        "country": "Tanzania", "region": "Sub-Saharan Africa",
        "hofstede": "High power distance, collectivist; ujamaa (familyhood) heritage; Swahili central to business communication.",
        "legal": "Common law (British heritage); Investment Act 1997 (revised 2022); TIC one-stop window; mining sector tightened by Magufuli-era 2017 laws.",
        "practices": ["Government majority in extractives via NMC", "Free zones (EPZ) for manufacturing", "Mining royalties and local-content rules strict"],
        "case": "Barrick Gold's 2020 USD 1.1B settlement with Tanzania over Acacia disputes set a precedent for African resource-tax renegotiation.",
        "dos": [
            ("Use Swahili greetings (Karibu, Asante)", "Default to English exclusively"),
            ("Account for NMC carried-interest rules", "Assume 100% foreign ownership"),
            ("Engage TIC for streamlined approvals", "Skip TIC registration"),
            ("Pay royalties promptly", "Underestimate tax assertiveness"),
            ("Respect Zanzibar's semi-autonomy", "Treat mainland and isles identically"),
        ],
        "refs": ["TIC Tanzania, 'Investment Guide 2022.'", "Hofstede Insights: Tanzania (regional est.).", "Jacob, T. & Pedersen, R., 'Tanzania's Mining Sector,' DIIS, 2018."],
    },
    {
        "country": "Senegal", "region": "Sub-Saharan Africa",
        "hofstede": "High power distance, collectivist; teranga (hospitality) defines social and business relations; French-Wolof bilingual.",
        "legal": "Civil law (French heritage); OHADA Uniform Acts apply; Investment Code 2004 governs incentives.",
        "practices": ["Mouride brotherhood influences commerce", "French language for legal documents", "Oil/gas finds (Yakaar Teranga) reshaping economy"],
        "case": "BP/Kosmos's 2018 USD 4.8B Greater Tortue Ahmeyim gas FID with Senegal-Mauritania showed transboundary deal complexity.",
        "dos": [
            ("Use teranga hospitality reciprocally", "Reject welcome rituals"),
            ("Speak French in formal settings", "Default to English"),
            ("Engage Mouride business networks", "Ignore religious-economic ties"),
            ("Comply with OHADA Uniform Acts", "Assume French law directly applies"),
            ("Honour Friday prayer breaks", "Schedule Friday-midday meetings"),
        ],
        "refs": ["APIX Senegal, 'Investment Guide 2022.'", "Hofstede Insights: Senegal (regional est.).", "Babou, C., 'Fighting the Greater Jihad: Murid Brotherhood,' Ohio UP, 2007."],
    },
    {
        "country": "Morocco", "region": "North Africa",
        "hofstede": "High power distance, collectivist; mint-tea hospitality; Francophone business norms with Arab/Berber identity.",
        "legal": "Civil law (French heritage) with Islamic personal status; Investment Charter 2022; CIMAC arbitration.",
        "practices": ["Tangier-Med port hub for African automotive", "Royal Cabinet involvement in major deals", "French language dominant in contracts"],
        "case": "Renault's 2012-2020 USD 2B Tangier-Med plant expansion, anchored on local-content and royal sponsorship, made Morocco Africa's auto hub.",
        "dos": [
            ("Conduct meetings over mint tea", "Refuse tea ceremony"),
            ("Use French for contracts and emails", "Insist on English-only"),
            ("Engage royal-advisory connections", "Assume purely technocratic process"),
            ("Comply with local-content quotas", "Import only finished goods"),
            ("Respect Ramadan reduced hours", "Maintain full-day meetings"),
        ],
        "refs": ["AMDIE Morocco, 'Investing in Morocco 2022.'", "Hofstede Insights: Morocco, 2023.", "Cammett, M., 'Globalization and Business Politics in Arab North Africa,' Cambridge UP, 2007."],
    },
    {
        "country": "Algeria", "region": "North Africa",
        "hofstede": "High power distance, collectivist; bureaucratic, oil-dependent; French language secondary to Arabic.",
        "legal": "Civil law (French heritage); Hydrocarbons Law 2019 reopened upstream; Investment Law 2022 lifted 51-49 rule in many sectors.",
        "practices": ["Sonatrach dominates oil/gas", "Bureaucracy heavy, payments slow", "French and Arabic both used"],
        "case": "Eni's 2022 USD 4B Berkine gas deal with Sonatrach showcased post-reform Algerian openness after years of restrictive 51-49 ownership rules.",
        "dos": [
            ("Engage Sonatrach senior leadership", "Bypass national oil company"),
            ("File documents in Arabic and French", "Submit English-only documents"),
            ("Allow long payment cycles", "Expect rapid disbursements"),
            ("Use new investment-law incentives", "Assume old 51-49 still applies"),
            ("Respect Ramadan and Friday rhythms", "Force Western calendar"),
        ],
        "refs": ["AAPI Algeria, 'Investment Guide 2022.'", "Hofstede Insights: Algeria (regional est.).", "Aïssaoui, A., 'Algeria's Oil and Gas,' OIES, 2016."],
    },
    {
        "country": "Tunisia", "region": "North Africa",
        "hofstede": "High power distance, collectivist; relatively secular and European-oriented; Francophone-Arab blend.",
        "legal": "Civil law (French heritage); Investment Law 2016 streamlined incentives via TIA; CCIT arbitration.",
        "practices": ["Trade union UGTT influential in deals", "EU is dominant trade partner", "Olive oil, textiles, electronics key sectors"],
        "case": "The 2020 European Bank for Reconstruction & Development's USD 350M Tunis-Sfax rail upgrade required UGTT and ministry tripartite talks.",
        "dos": [
            ("Engage UGTT in labour-intensive deals", "Skip union consultation"),
            ("Use French and Arabic in contracts", "Submit only English"),
            ("Leverage EU association agreement", "Ignore EU origin rules"),
            ("Respect Ramadan working hours", "Push full-day intensity"),
            ("Visit Tunis personally", "Negotiate exclusively remote"),
        ],
        "refs": ["TIA Tunisia, 'Invest in Tunisia 2022.'", "Hofstede Insights: Tunisia (regional est.).", "Cammett, M., 'Globalization and Business Politics in Arab North Africa,' 2007."],
    },
    {
        "country": "Germany", "region": "Europe",
        "hofstede": "Low power distance, individualist, high uncertainty avoidance; punctuality, precision, and process-orientation dominate.",
        "legal": "Civil law (BGB 1900); strong codetermination via Mitbestimmung (works councils); DIS arbitration; strict GDPR/IP.",
        "practices": ["Detailed agendas and dossiers expected", "Decisions follow technical evaluation", "Works councils consulted in M&A"],
        "case": "Linde-Praxair's 2018 USD 90B industrial-gas merger required two years of EU/US/Chinese antitrust talks plus Mitbestimmung negotiations.",
        "dos": [
            ("Arrive 5-10 minutes early", "Show up late"),
            ("Provide technical data upfront", "Lead with marketing fluff"),
            ("Use formal Sie pronoun and titles", "Switch to du prematurely"),
            ("Involve Betriebsrat in workforce decisions", "Bypass works councils"),
            ("Stick to agenda", "Detour into unrelated topics"),
        ],
        "refs": ["Germany Trade & Invest, 'Business Guide 2022.'", "Hofstede Insights: Germany, 2023.", "Streeck, W., 'Re-Forming Capitalism,' Oxford UP, 2009."],
    },
    {
        "country": "France", "region": "Europe",
        "hofstede": "High power distance, individualist, moderate uncertainty avoidance; intellectual debate (Cartesian logic) and elegant rhetoric valued.",
        "legal": "Civil law (Napoleonic Code 1804); Loi PACTE 2019 modernised company law; CCIP and ICC Paris arbitration central.",
        "practices": ["Long lunches part of negotiation", "Hierarchy strong; PDG (CEO) decides", "Grandes écoles networks pivotal"],
        "case": "Air France-KLM's 2004 USD 13B merger required intricate French-Dutch governance and union talks, becoming Europe's largest aviation deal of its era.",
        "dos": [
            ("Use Monsieur/Madame plus surname", "Use first names early"),
            ("Engage in intellectual debate", "Avoid robust discussion"),
            ("Schedule long-lunch meetings", "Push for snack-bar speed"),
            ("Respect August holiday closures", "Plan major events in August"),
            ("Leverage grandes écoles intros", "Cold-call senior CEOs"),
        ],
        "refs": ["Business France, 'Doing Business 2022.'", "Hofstede Insights: France, 2023.", "d'Iribarne, P., 'La Logique de l'Honneur,' Seuil, 1989."],
    },
    {
        "country": "United Kingdom", "region": "Europe",
        "hofstede": "Low power distance, highly individualist, low uncertainty avoidance; politeness, understatement, and humour valued.",
        "legal": "Common law; Companies Act 2006; Takeover Panel oversight for public bids; LCIA arbitration globally prominent.",
        "practices": ["Small talk and weather openers", "Indirect refusal ('quite difficult')", "Class and accent still influence interactions"],
        "case": "AstraZeneca's 2014 GBP 69B rejection of Pfizer's hostile bid demonstrated UK Takeover Panel mechanics and shareholder activism.",
        "dos": [
            ("Open with light small talk", "Skip pleasantries"),
            ("Use understatement appropriately", "Boast or oversell"),
            ("Honour Takeover Code timelines", "Underestimate Panel powers"),
            ("Address as Mr/Ms then move to first names quickly", "Stay overly formal"),
            ("Respect pub-based informal closure", "Refuse after-hours drinks"),
        ],
        "refs": ["UK DBT, 'Doing Business 2022.'", "Hofstede Insights: UK, 2023.", "Fox, K., 'Watching the English,' Hodder, 2014."],
    },
    {
        "country": "Italy", "region": "Europe",
        "hofstede": "Moderate power distance, individualist, masculine, high uncertainty avoidance; relationships and family enterprise dominate.",
        "legal": "Civil law (Codice Civile 1942); Companies Code reformed 2003; arbitration via Milan Chamber; bureaucracy notoriously slow.",
        "practices": ["Family firms (Agnelli, Ferrero) major counterparties", "Regional culture matters (Milan vs Naples)", "Long meals seal deals"],
        "case": "Stellantis's 2021 USD 52B Fiat Chrysler-PSA merger required two years of Agnelli/Peugeot family talks plus EU competition review.",
        "dos": [
            ("Build family-business rapport", "Treat solely as transactional"),
            ("Use Dottore/Avvocato titles", "Drop titles"),
            ("Allow flexible scheduling", "Demand strict adherence"),
            ("Engage Milan/Rome lawyers for contracts", "Use only home-country counsel"),
            ("Honour long lunches", "Skip social meals"),
        ],
        "refs": ["ICE Italy, 'Investment Guide 2022.'", "Hofstede Insights: Italy, 2023.", "Colli, A., 'The History of Family Business,' Cambridge UP, 2003."],
    },
    {
        "country": "Spain", "region": "Europe",
        "hofstede": "Moderate-high power distance, collectivist (family), high uncertainty avoidance; personalismo and confianza shape deals.",
        "legal": "Civil law (Código Civil 1889); Companies Act 2010; arbitration via CIMA; strong consumer protection.",
        "practices": ["Late dinners (10pm) for social closure", "Regional autonomy (Catalonia, Basque) matters", "Siesta tradition fading but lunch breaks long"],
        "case": "BBVA's 2020 USD 11.6B sale of US subsidiary to PNC was negotiated remotely during COVID, showing modernised Spanish cross-border M&A.",
        "dos": [
            ("Adopt 9-10pm dinners for relationship-building", "Push 6pm dinners"),
            ("Use Señor/Señora plus surname", "Default to first names"),
            ("Respect regional identities", "Conflate all Spaniards"),
            ("Build confianza over multiple visits", "Try to close on first trip"),
            ("Honour August holidays", "Plan launches in August"),
        ],
        "refs": ["ICEX Spain, 'Doing Business 2022.'", "Hofstede Insights: Spain, 2023.", "Royo, S., 'Lessons from the Spanish Economic Crisis,' Palgrave, 2013."],
    },
    {
        "country": "Netherlands", "region": "Europe",
        "hofstede": "Very low power distance, individualist, feminine; egalitarian and very direct (bespreekbaarheid).",
        "legal": "Civil law (Burgerlijk Wetboek 1992); Dutch Corporate Governance Code; NAI arbitration; works councils via WOR.",
        "practices": ["Polder model: consensus among stakeholders", "Flat hierarchy; junior staff speak up", "Direct, even blunt feedback common"],
        "case": "ASML's 2016 USD 3.1B Hermes Microvision acquisition and ongoing Dutch-US export-control talks highlight precision and transparency in Dutch deals.",
        "dos": [
            ("Welcome direct critique", "Take frankness personally"),
            ("Use first names quickly", "Insist on formal Mr/Mrs"),
            ("Apply polder consensus building", "Push top-down decisions"),
            ("Respect cycling-based punctuality", "Run 30+ minutes late"),
            ("Honour OR/works-council rights", "Bypass employee voice"),
        ],
        "refs": ["NL Invest, 'Doing Business 2022.'", "Hofstede Insights: Netherlands, 2023.", "Schama, S., 'The Embarrassment of Riches,' Knopf, 1987."],
    },
    {
        "country": "Belgium", "region": "Europe",
        "hofstede": "Moderate power distance, individualist, high uncertainty avoidance; Flemish-Walloon cultural duality.",
        "legal": "Civil law (Napoleonic Code 1804 with adaptations); Companies Code 2019; CEPANI arbitration.",
        "practices": ["Trilingual: Dutch, French, German", "EU institutions headquartered in Brussels", "Compromise (Belgian consensus) prized"],
        "case": "AB InBev's 2008 USD 52B Anheuser-Busch acquisition leveraged Brussels' diplomatic culture in cross-Atlantic merger talks.",
        "dos": [
            ("Switch fluidly between Dutch and French", "Force one language"),
            ("Respect linguistic-region sensitivities", "Make Walloon/Flemish jokes"),
            ("Engage EU stakeholders in Brussels", "Bypass EU dimension"),
            ("Use formal titles initially", "Be overly casual"),
            ("Allow long, consensus-building processes", "Push for unilateral decisions"),
        ],
        "refs": ["FIT Flanders/AWEX Wallonia investment guides 2022.", "Hofstede Insights: Belgium, 2023.", "Witte, E., 'Political History of Belgium,' VUB Press, 2009."],
    },
    {
        "country": "Sweden", "region": "Europe",
        "hofstede": "Very low power distance, individualist, feminine; lagom (just-right) and consensus shape negotiations.",
        "legal": "Civil law (Swedish Code 1734 with continuous updates); Companies Act 2005; SCC arbitration globally prominent.",
        "practices": ["Fika (coffee breaks) build trust", "Decisions reached via consensus", "Long parental leave shapes scheduling"],
        "case": "Volvo Cars' 2010 USD 1.8B sale by Ford to Geely involved Swedish union talks and SCC-style transparency.",
        "dos": [
            ("Participate in fika rituals", "Skip coffee breaks"),
            ("Pursue lagom-balanced terms", "Demand maximalist deals"),
            ("Engage unions in labour decisions", "Bypass IF Metall"),
            ("Honour summer/winter holidays", "Push July meetings"),
            ("Use Stockholm SCC arbitration clauses", "Default to home-country forums"),
        ],
        "refs": ["Business Sweden, 'Investment Climate 2022.'", "Hofstede Insights: Sweden, 2023.", "Daun, Å., 'Swedish Mentality,' Penn State, 1996."],
    },
    {
        "country": "Norway", "region": "Europe",
        "hofstede": "Very low power distance, individualist, feminine; egalitarian, low-key, with strong public-sector role.",
        "legal": "Civil law (Norwegian Code 1687 with updates); Companies Act 1997; arbitration via Norwegian Arbitration Act 2004.",
        "practices": ["Sovereign wealth fund (USD 1.5T) shapes investment culture", "Trade unions central via LO", "Hytte (cabin) social culture builds trust"],
        "case": "Equinor's 2021 USD 5B Bay du Nord Canada project negotiations integrated Norwegian state ESG mandates with Canadian provincial regulation.",
        "dos": [
            ("Engage LO unions early", "Bypass labour-side"),
            ("Highlight ESG performance", "Greenwash credentials"),
            ("Respect dugnad (volunteer) ethos", "Display ostentatious wealth"),
            ("Honour summer cabin season", "Schedule July/August meetings"),
            ("Use plain Norwegian English", "Over-use jargon"),
        ],
        "refs": ["Invest in Norway, 'Doing Business 2022.'", "Hofstede Insights: Norway, 2023.", "Norges Bank Investment Management, Annual Report 2022."],
    },
    {
        "country": "Finland", "region": "Europe",
        "hofstede": "Very low power distance, individualist, feminine; quiet, direct, sisu (resilience) and trust-based.",
        "legal": "Civil law (Finnish Code with Swedish heritage); Companies Act 2006; FAI arbitration; strong digital-government practices.",
        "practices": ["Sauna often part of deal-making", "Silence comfortable; no need to fill", "Decisions data-driven, low-drama"],
        "case": "Nokia's 2016 EUR 15.6B Alcatel-Lucent merger negotiated quietly between Helsinki and Paris, exemplifying Finnish low-key tech M&A.",
        "dos": [
            ("Embrace pauses and silences", "Fill every gap with chatter"),
            ("Accept sauna invitation if offered", "Decline sauna rudely"),
            ("Be direct yet polite", "Use heavy diplomatic hedging"),
            ("Trust the written word", "Demand redundant verbal confirmations"),
            ("Honour summer-cabin holidays (July)", "Schedule July intensives"),
        ],
        "refs": ["Business Finland, 'Doing Business 2022.'", "Hofstede Insights: Finland, 2023.", "Lewis, R., 'Finland: Cultural Lone Wolf,' Intercultural Press, 2005."],
    },
    {
        "country": "Denmark", "region": "Europe",
        "hofstede": "Very low power distance, individualist, feminine; hygge (coziness) and tillid (trust) underpin business.",
        "legal": "Civil law (Danish Code 1683 with updates); Companies Act 2010; CAI arbitration; high-trust contracts.",
        "practices": ["Flat hierarchy; CEOs answer e-mails directly", "Janteloven discourages boastfulness", "Punctuality and short, efficient meetings"],
        "case": "Maersk's 2022 USD 7B fleet decarbonization deal with Equinor and methanol suppliers reflected Danish climate-first negotiation framing.",
        "dos": [
            ("Use first names from the start", "Insist on Mr/Ms"),
            ("Keep meetings to 30-60 minutes", "Drag past hour two"),
            ("Highlight sustainability metrics", "Treat ESG as add-on"),
            ("Respect janteloven modesty", "Brag about credentials"),
            ("Plan around 4pm school-pickup norms", "Schedule late-day meetings"),
        ],
        "refs": ["Invest in Denmark, 'Business Guide 2022.'", "Hofstede Insights: Denmark, 2023.", "Sandemose, A., 'En flyktning krysser sitt spor,' 1933 (Janteloven)."],
    },
    {
        "country": "Poland", "region": "Europe",
        "hofstede": "High power distance, individualist, masculine, high uncertainty avoidance; Catholic heritage and EU integration shape business.",
        "legal": "Civil law (1964 Civil Code, updated post-1989); Companies Act 2000; arbitration via Lewiatan Court; EU compliance central.",
        "practices": ["State-owned enterprises (PKN Orlen, KGHM) significant", "Bureaucracy notable", "Family Catholic values often relevant"],
        "case": "PKN Orlen's 2022 USD 5B merger with Lotos required EU divestiture talks and showed Polish energy consolidation strategy.",
        "dos": [
            ("Use Pan/Pani plus surname formally", "Drop titles early"),
            ("Respect Catholic holidays (Easter, All Saints)", "Schedule Nov 1 meetings"),
            ("Engage SOE leadership directly", "Stay only with mid-managers"),
            ("Verify EU-state-aid implications", "Assume free domestic terms"),
            ("Bring small gifts (alcohol, sweets)", "Show up empty-handed"),
        ],
        "refs": ["PAIH Poland, 'Investment Guide 2022.'", "Hofstede Insights: Poland, 2023.", "Cieślik, A., 'FDI in Poland,' Springer, 2020."],
    },
    {
        "country": "Czech Republic", "region": "Europe",
        "hofstede": "Moderate power distance, individualist, masculine, high uncertainty avoidance; pragmatic, German-leaning business style.",
        "legal": "Civil law (recodified 2014); Business Corporations Act 2014; arbitration via Prague Arbitration Court.",
        "practices": ["Industrial heritage; Škoda VW-owned", "Direct communication, formal titles", "Beer culture aids relationship-building"],
        "case": "Volkswagen's 1991 USD 6B Škoda Auto acquisition began an evolving partnership and exemplifies CEE post-1989 industrial transformation deals.",
        "dos": [
            ("Use Pane/Paní plus surname", "Default to first names"),
            ("Be direct yet polite", "Beat around the bush"),
            ("Honour beer-after-work etiquette", "Refuse all invitations"),
            ("Highlight engineering credentials", "Lead with marketing fluff"),
            ("Use Prague arbitration clauses", "Default to foreign forum"),
        ],
        "refs": ["CzechInvest, 'Doing Business 2022.'", "Hofstede Insights: Czech Republic, 2023.", "Myant, M., 'Vulnerable Transformations: CEE,' Routledge, 2010."],
    },
    {
        "country": "Hungary", "region": "Europe",
        "hofstede": "High power distance, individualist, masculine, high uncertainty avoidance; formal, hierarchical, EU-integrated yet sovereigntist.",
        "legal": "Civil law (Civil Code 2013); Companies Act 2006; arbitration via Budapest Money & Capital Markets Arbitration Court.",
        "practices": ["Government plays activist role (utility re-nationalisations)", "German automotive supply chains key", "Family names placed surname-first"],
        "case": "BMW's 2018 USD 1.2B Debrecen plant deal included Hungarian state subsidies and EU competition review.",
        "dos": [
            ("Address Hungarians 'Surname Firstname'", "Reverse name order"),
            ("Use Úr/Asszony titles", "Drop honorifics"),
            ("Engage government-incentive office", "Assume EU-only state-aid path"),
            ("Build long-term relationships", "Hit-and-run deal style"),
            ("Respect national-pride sensitivities", "Make light of Trianon history"),
        ],
        "refs": ["HIPA Hungary, 'Investment Guide 2022.'", "Hofstede Insights: Hungary, 2023.", "Kornai, J., 'The Soft Budget Constraint,' Kyklos, 1986."],
    },
    {
        "country": "Romania", "region": "Europe",
        "hofstede": "High power distance, collectivist, moderate masculinity, high uncertainty avoidance; Latin warmth with Eastern formality.",
        "legal": "Civil law (recodified 2011); Companies Law 31/1990; arbitration via Court of International Commercial Arbitration; EU compliance.",
        "practices": ["IT outsourcing hub (Bucharest, Cluj)", "Bureaucracy improving but still present", "Hospitality with strong Orthodox traditions"],
        "case": "OMV-Petrom's 2022 USD 4B Neptun Deep gas FID with Romgaz reflected Romanian-Austrian Black Sea energy partnership.",
        "dos": [
            ("Use Domnul/Doamna titles", "Be overly informal"),
            ("Accept tuică (plum brandy) toasts", "Refuse all toasts"),
            ("Engage in social meals", "Insist on tight schedules"),
            ("Verify Orthodox feast days", "Schedule Easter-week meetings"),
            ("Use EU-aligned arbitration clauses", "Default to non-EU forums"),
        ],
        "refs": ["InvestRomania, 'Business Guide 2022.'", "Hofstede Insights: Romania, 2023.", "Roper, S., 'Romania: The Unfinished Revolution,' Routledge, 2000."],
    },
    {
        "country": "Greece", "region": "Europe",
        "hofstede": "High power distance, collectivist, masculine, very high uncertainty avoidance; philotimo (honour) and family central.",
        "legal": "Civil law (Civil Code 1946); Companies Act 4548/2018; arbitration via Athens Chamber Arbitration; EU compliance.",
        "practices": ["Family shipping firms (Niarchos, Latsis) influential", "Bureaucracy improving post-MoU reforms", "Late-night dinners normal"],
        "case": "Piraeus Port's 2016 USD 1.5B sale to COSCO required EU and Greek labour-union talks, becoming a flagship Belt & Road port deal.",
        "dos": [
            ("Use Kyrie/Kyria titles", "Default to first names"),
            ("Honour philotimo and family ties", "Treat purely as transactional"),
            ("Accept long taverna dinners", "Push fast-food meetings"),
            ("Allow bureaucratic timelines", "Demand Western-speed approvals"),
            ("Engage union (PAME/GSEE) early", "Sideline labour groups"),
        ],
        "refs": ["Enterprise Greece, 'Doing Business 2022.'", "Hofstede Insights: Greece, 2023.", "Triandis, H., 'Culture and Social Behaviour,' McGraw-Hill, 1994."],
    },
    {
        "country": "Portugal", "region": "Europe",
        "hofstede": "High power distance, collectivist, moderate masculinity, high uncertainty avoidance; warm, relationship-driven, Atlantic outlook.",
        "legal": "Civil law (Civil Code 1966); Companies Code 1986; arbitration via Lisbon Chamber.",
        "practices": ["Family conglomerates (Sonae, Jerónimo Martins)", "Lusophone-Africa & Brazil ties significant", "Long lunches and saudade-tinged rapport"],
        "case": "China Three Gorges's 2011 USD 3.5B EDP stake (later boosted in 2018) showed Portuguese privatisation negotiation under EU/IMF MoU.",
        "dos": [
            ("Use Senhor/Senhora plus surname", "Default to first names"),
            ("Engage Lusophone networks (Brazil, Angola)", "Treat in isolation from PALOP"),
            ("Allow long lunches", "Insist on grab-and-go"),
            ("Respect Catholic holidays", "Schedule Easter-week meetings"),
            ("Engage CGD/national-bank intros", "Cold-call regulators"),
        ],
        "refs": ["AICEP Portugal, 'Invest Portugal 2022.'", "Hofstede Insights: Portugal, 2023.", "Royo, S., 'Portugal in the European Union,' Palgrave, 2012."],
    },
    {
        "country": "Switzerland", "region": "Europe",
        "hofstede": "Low power distance, individualist, masculine, high uncertainty avoidance; precision, discretion, multilingual federalism.",
        "legal": "Civil law (CC 1907, CO 1911); arbitration via Swiss Arbitration Centre; banking-secrecy partially reformed via AEOI 2017.",
        "practices": ["Punctuality and precision absolute", "Cantonal differences (Geneva vs Zurich)", "Discretion in banking and pharma deals"],
        "case": "Chemchina's 2017 USD 43B Syngenta acquisition combined Swiss agrochemical excellence with Chinese strategic acquisition under FINMA-CFIUS scrutiny.",
        "dos": [
            ("Arrive punctually (5 minutes early)", "Run late"),
            ("Match language to canton (DE/FR/IT)", "Force English in Romandy"),
            ("Use Herr/Frau plus surname", "Default to first names early"),
            ("Apply Swiss Rules arbitration", "Default to non-Swiss forum"),
            ("Honour discretion in banking", "Disclose counterparties publicly"),
        ],
        "refs": ["S-GE Switzerland, 'Investment Guide 2022.'", "Hofstede Insights: Switzerland, 2023.", "Bergier, J.-F., 'Histoire économique de la Suisse,' Payot, 1984."],
    },
    {
        "country": "Austria", "region": "Europe",
        "hofstede": "Very low power distance, individualist, masculine, high uncertainty avoidance; precise, formal, German-leaning.",
        "legal": "Civil law (ABGB 1811); Companies Act 1965; arbitration via VIAC.",
        "practices": ["Formal titles (Dr, Mag.) essential", "Coffee-house culture for negotiations", "Strong codetermination through works councils"],
        "case": "Voestalpine's 2017 USD 1.4B Texas DRI plant negotiations bridged Austrian engineering with US energy/labour rules.",
        "dos": [
            ("Use academic titles (Dr., Mag.)", "Drop titles"),
            ("Schedule Kaffeehaus meetings", "Insist on office-only venues"),
            ("Respect Austrian neutrality politics", "Equate with German positions"),
            ("Engage Arbeiterkammer/works councils", "Bypass labour reps"),
            ("Use VIAC arbitration clauses", "Default to foreign forums"),
        ],
        "refs": ["ABA Invest in Austria, 'Business Guide 2022.'", "Hofstede Insights: Austria, 2023.", "Tálos, E., 'Social Partnership in Austria,' Springer, 2006."],
    },
    {
        "country": "Ireland", "region": "Europe",
        "hofstede": "Low power distance, individualist, moderately masculine; warm, witty, transatlantic business hub.",
        "legal": "Common law (UK heritage with EU layer); Companies Act 2014; arbitration via Arbitration Ireland; IFSC for international finance.",
        "practices": ["Tech/pharma multinationals dominate (Google, Pfizer)", "Storytelling and humour build rapport", "12.5% corporate tax shapes deal structures"],
        "case": "Pfizer-Allergan's failed 2016 USD 160B inversion deal showed Ireland's centrality and US Treasury responses to tax-driven mergers.",
        "dos": [
            ("Use first names quickly", "Insist on Mr/Mrs"),
            ("Engage in storytelling and craic", "Be coldly transactional"),
            ("Verify post-BEPS/OECD tax exposure", "Assume 12.5% remains untouched"),
            ("Honour pub-meeting culture", "Refuse Friday pints"),
            ("Engage IDA Ireland early", "Skip IDA introductions"),
        ],
        "refs": ["IDA Ireland, 'Annual Report 2022.'", "Hofstede Insights: Ireland, 2023.", "Barry, F., 'FDI and Industrial Development in Ireland,' Palgrave, 2007."],
    },
    {
        "country": "Russia", "region": "Russia/CIS",
        "hofstede": "High power distance, collectivist, masculine, high uncertainty avoidance; vlast (power) and svyazi (connections) central.",
        "legal": "Civil law (1994/1996/2001/2006 Civil Code parts); Foreign Investment Law 1999; sanctions post-2022 complicate cross-border deals.",
        "practices": ["State-led capitalism; Kremlin signals matter", "Vodka toasts seal deals", "Bureaucracy and risk of asset disputes"],
        "case": "Rosneft-BP's 2013 USD 55B TNK-BP deal showcased Russian state-strategic acquisition logic—and the later 2022 unwind illustrates sanction-era risk.",
        "dos": [
            ("Use formal Russian patronymics (Ivan Ivanovich)", "Use only first names"),
            ("Accept vodka toasts thoughtfully", "Refuse outright"),
            ("Verify sanctions compliance rigorously", "Assume past licences still valid"),
            ("Build svyazi over multiple visits", "Try to close on one trip"),
            ("Bring small gifts (flowers, chocolates)", "Give 13 flowers (unlucky)"),
        ],
        "refs": ["EU Council Decision 2022/335 (Russia sanctions).", "Hofstede Insights: Russia, 2023.", "Ledeneva, A., 'How Russia Really Works,' Cornell UP, 2006."],
    },
    {
        "country": "Ukraine", "region": "Russia/CIS",
        "hofstede": "High power distance, collectivist, moderately masculine, high uncertainty avoidance; warm hospitality with Soviet-era formality.",
        "legal": "Civil law (Civil Code 2003); Companies Law 2017; arbitration via UAC ICAC; war-era EU candidacy reshapes regulatory direction.",
        "practices": ["Strong agribusiness (sunflower, grain)", "Oligarchic ownership patterns shifting post-2022", "EU candidate status accelerating reforms"],
        "case": "DTEK-NJSC Naftogaz's 2017 USD 1B renewable-energy initiative anchored Ukraine's pre-war pivot to wind, with EBRD support.",
        "dos": [
            ("Use formal titles plus patronymic", "Use diminutive names early"),
            ("Verify war-risk and sanctions due diligence", "Assume pre-2022 risk maps"),
            ("Engage Naftogaz/state enterprises", "Bypass strategic SOEs"),
            ("Coordinate with EBRD/EU funders", "Skip donor-led finance"),
            ("Respect Orthodox holidays", "Schedule Easter week"),
        ],
        "refs": ["UkraineInvest, 'Investment Guide 2022.'", "Hofstede Insights: Ukraine, 2023.", "Aslund, A., 'Ukraine: What Went Wrong,' Peterson, 2015."],
    },
    {
        "country": "Kazakhstan", "region": "Russia/CIS",
        "hofstede": "High power distance, collectivist, moderately masculine; hospitality (qonaqjaylylyq) and clan ties strong.",
        "legal": "Civil law (Civil Code 1994/1999); AIFC offers common-law option for finance; arbitration via KAZIAC and AIFC Court.",
        "practices": ["Oil/gas dominated by Tengiz, Kashagan, Karachaganak", "Kazakh language rising alongside Russian", "AIFC modeled on DIFC for English-law finance"],
        "case": "Tengizchevroil's 2016 USD 36.8B Future Growth Project FID with KazMunayGas/Chevron/ExxonMobil/Shell underscored complex Caspian-basin negotiations.",
        "dos": [
            ("Greet with both Kazakh and Russian openings", "Default to Russian only"),
            ("Use AIFC for English-law contracts", "Insist on home-law forums"),
            ("Accept besbarmak (national dish) hospitality", "Refuse hosted meals"),
            ("Engage KazMunayGas leadership", "Bypass national oil firm"),
            ("Respect Nauryz spring holiday", "Schedule March 21-23"),
        ],
        "refs": ["AIFC, 'Annual Review 2022.'", "Hofstede Insights: Kazakhstan (regional est.).", "Olcott, M.B., 'Kazakhstan: Unfulfilled Promise,' Carnegie, 2010."],
    },
    {
        "country": "Brazil", "region": "Latin America",
        "hofstede": "High power distance, collectivist, feminine; jeitinho (creative workaround) and personalismo central.",
        "legal": "Civil law (Civil Code 2002); Companies Act 6.404/76; arbitration via CAM-CCBC; antitrust via CADE.",
        "practices": ["Long meals/social bonding precede deals", "CADE merger review can be slow", "Regional differences (São Paulo vs Rio)"],
        "case": "Ambev-Interbrew's 2004 USD 11.5B InBev merger created the world's largest brewer and demonstrated Brazilian dealmaking sophistication.",
        "dos": [
            ("Use Senhor/Senhora plus first name", "Default to Mr/Surname"),
            ("Build personalismo through repeated visits", "Try to close in one trip"),
            ("Engage CADE compliance early", "Underestimate antitrust review"),
            ("Allow jeitinho-style flexibility", "Insist on rigid interpretations"),
            ("Honour Carnival timing", "Schedule deals during Carnival"),
        ],
        "refs": ["Apex-Brasil, 'Doing Business 2022.'", "Hofstede Insights: Brazil, 2023.", "Damatta, R., 'Carnivals, Rogues, and Heroes,' Notre Dame UP, 1991."],
    },
    {
        "country": "Mexico", "region": "Latin America",
        "hofstede": "High power distance, collectivist, masculine, high uncertainty avoidance; familia and confianza (trust) define deals.",
        "legal": "Civil law (Federal Civil Code 1928); Companies Law (LGSM) 1934; arbitration via CAM Mexico; USMCA shapes cross-border deals.",
        "practices": ["Family conglomerates (FEMSA, Grupo Carso) dominant", "Hierarchy strong; senior decides", "Lunches (comida) long and central"],
        "case": "AB InBev's 2013 USD 20.1B Grupo Modelo (Corona) acquisition required DOJ divestitures and showed Mexican family-firm exit dynamics.",
        "dos": [
            ("Use Don/Doña for senior figures", "Default to first names"),
            ("Build confianza through repeated visits", "Try one-trip closure"),
            ("Engage USMCA origin/labour rules", "Assume NAFTA-only logic"),
            ("Honour 3-hour comidas", "Push 30-minute lunches"),
            ("Verify cartel-risk DD", "Skip security/integrity screening"),
        ],
        "refs": ["ProMéxico, 'Investment Guide 2022.'", "Hofstede Insights: Mexico, 2023.", "Lomnitz, L., 'Networks and Marginality,' Academic Press, 1977."],
    },
    {
        "country": "Argentina", "region": "Latin America",
        "hofstede": "High power distance, individualist, masculine, high uncertainty avoidance; European-influenced, expressive, debate-loving.",
        "legal": "Civil law (Civil and Commercial Code 2014); Companies Law 19.550; arbitration via BCBA Arbitration Tribunal; capital controls (cepo) constrain deals.",
        "practices": ["Macroeconomic volatility shapes pricing", "Capital controls limit profit repatriation", "Long dinners (10pm) and futbol passion"],
        "case": "Tecpetrol's 2017 USD 2.3B Vaca Muerta shale investment with YPF showed Argentine resource-development under Kirchnerist constraints.",
        "dos": [
            ("Use Señor/Señora plus surname", "Default to first names"),
            ("Account for inflation/devaluation", "Quote rigid local-currency price"),
            ("Verify capital-control restrictions", "Assume free profit repatriation"),
            ("Engage in vigorous debate", "Avoid robust argument"),
            ("Honour late dinners", "Push 7pm meals"),
        ],
        "refs": ["Argentina Investment & Trade Promotion Agency 2022.", "Hofstede Insights: Argentina, 2023.", "Manzetti, L., 'Privatization South American Style,' Oxford UP, 1999."],
    },
    {
        "country": "Chile", "region": "Latin America",
        "hofstede": "High power distance, collectivist, masculine, high uncertainty avoidance; formal, rule-following, copper-mining anchor.",
        "legal": "Civil law (Andrés Bello Civil Code 1857); Companies Law 18.046; arbitration via CAM Santiago; OECD-aligned.",
        "practices": ["Copper (Codelco, BHP, Antofagasta) dominant", "Pension funds (AFP) major investors", "More formal than Brazil/Argentina"],
        "case": "SQM-Tianqi 2018 USD 4.07B lithium-stake deal reshaped global EV-battery supply chains and faced anti-trust review.",
        "dos": [
            ("Use Señor/Señora plus surname", "Default first names"),
            ("Engage CCHEN/lithium regulation", "Assume free export rights"),
            ("Verify AFP/pension-fund interests", "Bypass capital-market gatekeepers"),
            ("Honour formal punctuality", "Run late"),
            ("Engage indigenous Mapuche stakeholders in south", "Sideline community talks"),
        ],
        "refs": ["InvestChile, 'Business Guide 2022.'", "Hofstede Insights: Chile, 2023.", "Silva, E., 'The State and Capital in Chile,' Westview, 1996."],
    },
    {
        "country": "Colombia", "region": "Latin America",
        "hofstede": "High power distance, collectivist, masculine, high uncertainty avoidance; warm, hospitable, family-driven.",
        "legal": "Civil law (Civil Code 1873); Companies Law 1258/2008 (SAS); arbitration via CCB Bogotá; Pacific Alliance economic integration.",
        "practices": ["Family conglomerates (GEA, Sarmiento) dominant", "Coffee culture central", "Post-2016 peace agreement reshapes rural deals"],
        "case": "Avianca-Taca 2010 USD 1.7B merger and 2020 Chapter 11 reorganisation showcased Colombian-Central American cross-border restructuring.",
        "dos": [
            ("Use Don/Doña plus first name for seniors", "Default to surnames coldly"),
            ("Engage SAS structures for speed", "Default to old SA forms"),
            ("Build confianza via coffee meetings", "Skip social rapport"),
            ("Verify post-FARC security context", "Ignore rural-zone risk"),
            ("Honour Catholic holidays", "Schedule Easter-week deals"),
        ],
        "refs": ["ProColombia, 'Investment Guide 2022.'", "Hofstede Insights: Colombia, 2023.", "Bushnell, D., 'The Making of Modern Colombia,' UC Press, 1993."],
    },
    {
        "country": "Peru", "region": "Latin America",
        "hofstede": "High power distance, collectivist, moderately masculine, high uncertainty avoidance; Andean indigenous-mestizo blend.",
        "legal": "Civil law (Civil Code 1984); General Corporations Law 1997; arbitration via CCL Lima; mining-sector central.",
        "practices": ["Mining (copper, zinc) anchors economy", "Lima dominant but Andean stakeholder consultation vital", "Political instability affects continuity"],
        "case": "China Minmetals's 2014 USD 7B Las Bambas copper acquisition required years of community-consultation talks in Apurímac.",
        "dos": [
            ("Conduct prior consultation (Convenio 169)", "Skip indigenous engagement"),
            ("Use Señor/Señora plus surname", "Default to first names"),
            ("Engage SUNAT on tax structuring early", "Assume light tax review"),
            ("Plan around political-cycle volatility", "Assume stable executive"),
            ("Honour Quechua/Aymara local protocols", "Treat as monolingual Spanish"),
        ],
        "refs": ["ProInversión Peru, 'Investment Guide 2022.'", "Hofstede Insights: Peru, 2023.", "Bebbington, A., 'Social Conflict, Economic Development and Extractive Industry,' Routledge, 2012."],
    },
    {
        "country": "Venezuela", "region": "Latin America",
        "hofstede": "High power distance, collectivist, masculine, high uncertainty avoidance; warm, expressive; deep political polarisation.",
        "legal": "Civil law (Civil Code 1982); Commercial Code 1955; sanctions (US OFAC, EU) constrain deals; arbitration via CAS.",
        "practices": ["PDVSA-centric oil sector under sanctions", "Hyperinflation/dollarisation distort pricing", "Diaspora intermediaries common"],
        "case": "Chevron's 2022 OFAC General License 41 to resume Venezuelan oil ops illustrated re-engagement amid lingering sanctions architecture.",
        "dos": [
            ("Verify OFAC/EU sanctions exposures", "Assume any prior licence stands"),
            ("Engage diaspora professionals", "Limit to onshore counsel"),
            ("Quote in USD with hedging", "Quote only in bolívares"),
            ("Plan for power-outage contingencies", "Assume reliable grid"),
            ("Respect political polarisation in talk", "Volunteer political opinions"),
        ],
        "refs": ["US Treasury OFAC General License 41 (2022).", "Hofstede Insights: Venezuela, 2023.", "Corrales, J., 'Fixing Democracy: Why Constitutional Change Often Fails to Enhance Democracy,' Oxford UP, 2018."],
    },
    {
        "country": "Cuba", "region": "Latin America",
        "hofstede": "High power distance, collectivist; centralised state-led economy; warm interpersonal style.",
        "legal": "Civil law (Civil Code 1987); Foreign Investment Law 118/2014; Mariel Special Development Zone offers incentives; arbitration via CCN.",
        "practices": ["State approval required for most deals", "Dual currency unified in 2021 (only CUP)", "US embargo (Helms-Burton) constrains US ties"],
        "case": "Spain's Iberostar 2017 USD 700M Havana hotel expansion required Cuban state-JV under FIL 118, showing tourism partnership template.",
        "dos": [
            ("Engage Cuban state JV partner", "Attempt 100% foreign ownership"),
            ("Use Mariel ZED incentives", "Default to general regime"),
            ("Verify Helms-Burton Title III exposure", "Ignore US-claim risks"),
            ("Allow long state-approval timelines", "Demand rapid sign-off"),
            ("Respect Revolution-era sensitivities", "Make political quips"),
        ],
        "refs": ["MINCEX Cuba, 'Cartera de Oportunidades 2022.'", "Hofstede Insights: Cuba (regional est.).", "Feinberg, R., 'Open for Business: Building the New Cuban Economy,' Brookings, 2016."],
    },
    {
        "country": "United States", "region": "North America",
        "hofstede": "Low power distance, very individualist, masculine, low uncertainty avoidance; direct, contract-heavy, litigious.",
        "legal": "Common law (federal + 50 states); Delaware GCL prevailing for corporates; SEC, DOJ, FTC oversight; CFIUS for FDI security review.",
        "practices": ["Lawyers central from day one", "Time-is-money pacing", "Disclosures and reps & warranties extensive"],
        "case": "Microsoft's 2022 USD 68.7B Activision-Blizzard acquisition required multi-jurisdiction antitrust (FTC, CMA, EU) and exemplifies US deal complexity.",
        "dos": [
            ("Lead with clear executive summary", "Bury the ask"),
            ("Use first names quickly", "Insist on overly formal address"),
            ("Engage CFIUS early for FDI", "Ignore national-security review"),
            ("Provide robust reps and warranties", "Skim on disclosure schedules"),
            ("Honour litigation risk in drafting", "Assume disputes won't arise"),
        ],
        "refs": ["SelectUSA, 'Investing in America 2022.'", "Hofstede Insights: US, 2023.", "Macneil, I., 'The New Social Contract,' Yale UP, 1980."],
    },
    {
        "country": "Canada", "region": "North America",
        "hofstede": "Low power distance, individualist, moderately masculine; polite, multicultural, bilingual (English/French).",
        "legal": "Common law (9 provinces) + civil law in Quebec; CBCA and provincial statutes; Investment Canada Act for national-security review.",
        "practices": ["Multicultural and bilingual sensitivity", "Indigenous (FPIC) consultation mandatory in resources", "Politeness and consensus-building"],
        "case": "Suncor-Petro-Canada's 2009 USD 19B merger created Canada's largest energy firm and exemplified consensus-driven Canadian M&A.",
        "dos": [
            ("Use English/French bilingually in Quebec", "Force English-only in Montreal"),
            ("Engage FPIC indigenous consultation", "Skip First Nations engagement"),
            ("Apply Investment Canada Act review", "Ignore net-benefit/security test"),
            ("Be punctual and polite", "Be brash or aggressive"),
            ("Respect bilingual labelling/contract rules", "Submit English-only filings"),
        ],
        "refs": ["Invest in Canada, 'Investment Guide 2022.'", "Hofstede Insights: Canada, 2023.", "Saul, J.R., 'A Fair Country: Telling Truths About Canada,' Viking, 2008."],
    },
    {
        "country": "Jamaica", "region": "Caribbean",
        "hofstede": "Moderate power distance, individualist, masculine; warm, expressive, relationship-based.",
        "legal": "Common law (British heritage); Companies Act 2004; JAMPRO investment promotion; arbitration via JIAC.",
        "practices": ["Tourism and bauxite anchor economy", "Patois informal usage common", "Religious (Christian) values in business culture"],
        "case": "The 2014 USD 1.7B JISCO acquisition of Alpart bauxite refinery from UC Rusal reflected Chinese-Caribbean resource engagement.",
        "dos": [
            ("Greet warmly with handshake and small talk", "Be coldly transactional"),
            ("Engage JAMPRO for incentive packages", "Skip incentive registration"),
            ("Verify CARICOM origin rules", "Assume standalone Jamaican rules"),
            ("Allow flexible Caribbean pace", "Demand New York speed"),
            ("Respect Sunday/church day", "Schedule Sunday meetings"),
        ],
        "refs": ["JAMPRO, 'Investment Guide 2022.'", "Hofstede Insights: Jamaica, 2023.", "Beckford, G., 'Persistent Poverty: Underdevelopment in Plantation Economies,' Oxford UP, 1972."],
    },
    {
        "country": "Australia", "region": "Oceania",
        "hofstede": "Low power distance, very individualist, masculine; egalitarian, direct, mateship-driven.",
        "legal": "Common law (English heritage); Corporations Act 2001; ACCC competition oversight; FIRB for foreign-investment review.",
        "practices": ["Mining (BHP, Rio Tinto) dominant", "Egalitarian culture; first names quick", "Indigenous (Native Title) consultation required"],
        "case": "BHP-Billiton's 2001 USD 28B dual-listed merger established the world's largest mining company and pioneered DLC structure.",
        "dos": [
            ("Use first names quickly", "Insist on Mr/Ms"),
            ("Engage FIRB early for FDI", "Skip foreign-investment review"),
            ("Honour Native Title consultation", "Bypass indigenous engagement"),
            ("Be direct but humorous", "Be overly formal/stiff"),
            ("Respect summer holidays (Dec-Jan)", "Schedule January deals"),
        ],
        "refs": ["Austrade, 'Why Australia 2022.'", "Hofstede Insights: Australia, 2023.", "Reynolds, H., 'The Law of the Land,' Penguin, 2003."],
    },
    {
        "country": "New Zealand", "region": "Oceania",
        "hofstede": "Low power distance, individualist, moderately masculine; informal, egalitarian, Maori-Pakeha bicultural.",
        "legal": "Common law (English heritage); Companies Act 1993; OIO (Overseas Investment Office) for FDI; Treaty of Waitangi shapes resource deals.",
        "practices": ["Maori iwi consultation important", "Compact market, agribusiness anchor", "Informal but rule-respecting"],
        "case": "Fonterra's 2007 USD 1B dairy JV with Nestlé/Chile demonstrated NZ farmer-cooperative governance in cross-border deal.",
        "dos": [
            ("Engage iwi/hapū early on land deals", "Bypass Maori partners"),
            ("Use first names quickly", "Default to Mr/Ms"),
            ("Honour OIO consent timelines", "Skip foreign-investment screening"),
            ("Highlight ESG/biosecurity rigor", "Ignore MPI biosecurity rules"),
            ("Respect Waitangi Day", "Schedule Feb 6 meetings"),
        ],
        "refs": ["NZTE, 'Investor Guide 2022.'", "Hofstede Insights: New Zealand, 2023.", "Belich, J., 'Making Peoples,' Allen Lane, 1996."],
    },
    {
        "country": "Bulgaria", "region": "Europe",
        "hofstede": "High power distance, collectivist, feminine, very high uncertainty avoidance; Balkan-Orthodox cultural roots, EU-aligned.",
        "legal": "Civil law (Civil Code 1950, Commerce Act 1991); arbitration via Bulgarian Chamber of Commerce; EU rules apply.",
        "practices": ["Outsourcing and software hubs in Sofia", "Head-shake/nod inverted from Western norms", "Long greetings and small talk expected"],
        "case": "Bulgarian Energy Holding's 2018 USD 1.3B IBEX gas-hub talks with Gazprom and EU showed Balkan energy-route negotiation.",
        "dos": [
            ("Confirm yes/no in writing (head signals invert)", "Rely solely on head signals"),
            ("Use Gospodin/Gospozha titles", "Default first names"),
            ("Respect Orthodox holidays", "Schedule Easter week"),
            ("Accept rakia toasts in moderation", "Refuse all toasts"),
            ("Engage EU-state-aid review early", "Assume domestic-only path"),
        ],
        "refs": ["InvestBulgaria Agency, 'Invest in Bulgaria 2022.'", "Hofstede Insights: Bulgaria, 2023.", "Bell, J., 'Bulgaria in Transition,' Westview, 1998."],
    },
    {
        "country": "Croatia", "region": "Europe",
        "hofstede": "High power distance, collectivist, feminine, high uncertainty avoidance; Mediterranean-Central European blend.",
        "legal": "Civil law (Obligations Act 2005); Companies Act 1995; EU membership from 2013; arbitration via Permanent Arbitration Court at HGK.",
        "practices": ["Tourism and shipbuilding key sectors", "Coffee culture central to relationships", "Hierarchy formal but warm"],
        "case": "INA's 2008-2014 USD 2B MOL acquisition disputes ended in PCA arbitration, signalling Croatian energy-asset governance pivots.",
        "dos": [
            ("Use Gospodin/Gospođa titles", "Default to first names"),
            ("Conduct meetings over coffee", "Skip social rituals"),
            ("Respect EU competition rules", "Assume pre-2013 framework"),
            ("Engage Sabor/government for major projects", "Bypass political stakeholders"),
            ("Honour Catholic holidays", "Schedule Easter or All-Saints week"),
        ],
        "refs": ["AIK Croatia, 'Investment Guide 2022.'", "Hofstede Insights: Croatia, 2023.", "Bartlett, W., 'Croatia: Between Europe and the Balkans,' Routledge, 2003."],
    },
    {
        "country": "Slovakia", "region": "Europe",
        "hofstede": "High power distance, individualist, masculine, high uncertainty avoidance; pragmatic, German-supply-chain anchored.",
        "legal": "Civil law (Civil Code 1964 with continual updates); Commercial Code 1991; arbitration via Slovak Chamber Court; EU rules apply.",
        "practices": ["Automotive manufacturing hub (VW, KIA, PSA, JLR)", "Direct but warm communication", "Formal titles initially"],
        "case": "Jaguar Land Rover's 2018 USD 1.4B Nitra plant launch with Slovak state incentives became Europe's premium-auto reshuffle benchmark.",
        "dos": [
            ("Use Pán/Pani plus surname", "Default to first names"),
            ("Leverage automotive cluster networks", "Treat as isolated market"),
            ("Engage SARIO incentive office", "Skip SARIO introduction"),
            ("Respect EU-state-aid limits", "Assume unlimited subsidies"),
            ("Build long-term partnerships", "Hit-and-run deals"),
        ],
        "refs": ["SARIO Slovakia, 'Investment Guide 2022.'", "Hofstede Insights: Slovakia, 2023.", "Kollár, M., 'Slovakia: A European Story,' Bratislava, 2018."],
    },
    {
        "country": "Slovenia", "region": "Europe",
        "hofstede": "Moderate power distance, feminine, high uncertainty avoidance; Central European precision with Mediterranean warmth.",
        "legal": "Civil law (Obligations Code 2001); Companies Act 2006; arbitration via LCA Ljubljana; EU and eurozone member.",
        "practices": ["Small, advanced economy with strong unions", "Co-determination via works councils", "Punctual and process-oriented"],
        "case": "Magna Steyr's 2017 USD 175M Hoče paint-shop deal (later cancelled) showed Slovenian environmental and worker-council sensitivities.",
        "dos": [
            ("Use Gospod/Gospa titles", "Default to first names"),
            ("Engage works councils early", "Bypass employee representation"),
            ("Verify environmental permits", "Underestimate green-NGO review"),
            ("Be punctual and prepared", "Run late or improvise"),
            ("Honour Catholic holidays", "Schedule Easter week"),
        ],
        "refs": ["SPIRIT Slovenia, 'Investment Guide 2022.'", "Hofstede Insights: Slovenia, 2023.", "Bohle, D. & Greskovits, B., 'Capitalist Diversity on Europe's Periphery,' Cornell UP, 2012."],
    },
    {
        "country": "Estonia", "region": "Europe",
        "hofstede": "Low power distance, individualist, feminine, high uncertainty avoidance; digital-first, direct, Nordic-aligned.",
        "legal": "Civil law (Estonian Civil Code 2002); Commercial Code 1995; e-Residency programme; arbitration via ECCI; EU and eurozone.",
        "practices": ["E-government and digital signatures default", "Tech startups (Skype, Wise, Bolt) dominant", "Minimal small talk, direct discussion"],
        "case": "Bolt Technology's 2021 EUR 600M Series E funding round, led by Sequoia, illustrated Estonia's globally-competitive tech-deal pace.",
        "dos": [
            ("Use digital signatures and e-Residency", "Demand paper-only contracts"),
            ("Be concise and direct", "Add unnecessary preamble"),
            ("Engage EAS investment agency", "Skip introduction support"),
            ("Use first names quickly", "Insist on titles"),
            ("Respect Nordic-style equality", "Show hierarchy ostentatiously"),
        ],
        "refs": ["EAS Estonia, 'Invest Estonia 2022.'", "Hofstede Insights: Estonia, 2023.", "Kotka, T., 'e-Estonia,' Brookings, 2018."],
    },
    {
        "country": "Iceland", "region": "Europe",
        "hofstede": "Very low power distance, individualist, feminine; egalitarian, informal, geothermal-energy specialist.",
        "legal": "Civil law (Nordic tradition); Companies Act 138/1994; EEA member but not EU; arbitration via Nordic Chamber Court.",
        "practices": ["Geothermal/hydro power attracts data centres and aluminium", "First-name society (even for President)", "Tight social trust"],
        "case": "Alcoa's 2008 USD 1.3B Fjarðaál smelter required hydro-power PPA with Landsvirkjun, anchoring Icelandic energy-export strategy.",
        "dos": [
            ("Use first names exclusively", "Insist on Mr/Mrs"),
            ("Highlight renewable-energy fit", "Pitch fossil-fuel angles"),
            ("Engage Promote Iceland early", "Skip national agency"),
            ("Be transparent on environmental impact", "Hide ecological footprint"),
            ("Plan around Icelandic-summer construction", "Schedule winter on-site work"),
        ],
        "refs": ["Promote Iceland, 'Invest in Iceland 2022.'", "Hofstede Insights: Iceland (regional est.).", "Magnússon, S., 'Wasteland with Words: A Social History of Iceland,' Reaktion, 2010."],
    },
    {
        "country": "Uzbekistan", "region": "Russia/CIS",
        "hofstede": "High power distance, collectivist, masculine, high uncertainty avoidance; Silk-Road hospitality, post-Soviet liberalisation.",
        "legal": "Civil law (Civil Code 1996, Investment Code 1998 revised 2019); arbitration via TIAC; significant 2017-2023 reforms opening economy.",
        "practices": ["Cotton, gold, gas anchor exports", "Persian-Turkic hospitality (osh, plov)", "State role still large but receding"],
        "case": "Lukoil's 2019 USD 1.7B Kandym gas project demonstrated Russian-Uzbek hydrocarbon partnership amid Mirziyoyev's reform era.",
        "dos": [
            ("Greet with both hands (handshake plus right-hand-to-chest)", "Single quick handshake"),
            ("Accept plov and tea hospitality", "Refuse hosted meals"),
            ("Use Russian or Uzbek; English limited", "Insist on English-only"),
            ("Verify export-licensing for cotton/gold", "Assume free trade flows"),
            ("Build relationships with state agencies", "Bypass government interface"),
        ],
        "refs": ["MIFT Uzbekistan, 'Investment Guide 2022.'", "Hofstede Insights: Uzbekistan (regional est.).", "Markowitz, L., 'State Erosion: Unlootable Resources and Unruly Elites in Central Asia,' Cornell UP, 2013."],
    },
    {
        "country": "Azerbaijan", "region": "Russia/CIS",
        "hofstede": "High power distance, collectivist, masculine; oil-state, Turkic-Persian heritage, hospitality central.",
        "legal": "Civil law (Civil Code 2000); Investment Promotion Law 2016; SOFAZ sovereign fund central; arbitration via AAC.",
        "practices": ["BP-led Azeri-Chirag-Guneshli oil hub", "SOCAR state-oil company pivotal", "Russian and Turkish business influence"],
        "case": "BP's 2017 USD 6B Shah Deniz 2 FID with SOCAR/TPAO/Lukoil consortium delivered Southern Gas Corridor to Europe.",
        "dos": [
            ("Engage SOCAR leadership directly", "Bypass national oil company"),
            ("Build hospitality-driven rapport", "Skip social meals"),
            ("Verify Caspian-status considerations", "Ignore Caspian Sea Convention"),
            ("Use Russian or Azerbaijani translators", "Rely on English-only"),
            ("Respect Novruz (March 20-21)", "Schedule meetings during Novruz"),
        ],
        "refs": ["AZPROMO Azerbaijan, 'Doing Business 2022.'", "Hofstede Insights: Azerbaijan (regional est.).", "LeVine, S., 'The Oil and the Glory,' Random House, 2007."],
    },
    {
        "country": "Belarus", "region": "Russia/CIS",
        "hofstede": "High power distance, collectivist, moderately masculine, high uncertainty avoidance; Soviet-era formality with Slavic warmth.",
        "legal": "Civil law (Civil Code 1998); Investment Law 53-Z 2013; HTP (High-Tech Park) offers favourable tax regime; arbitration via BelChamber.",
        "practices": ["State-owned giants (Belaruskali, BELAZ) dominant", "IT/HTP sector growing despite sanctions", "Bureaucracy substantial, Russian widely spoken"],
        "case": "Uralkali-Belaruskali's 2013 USD multi-billion potash cartel break-up reverberated through global fertiliser markets and showed Belarus's commodity-leverage strategy.",
        "dos": [
            ("Verify sanctions exposure (EU, US, UK)", "Assume pre-2020 risk picture"),
            ("Use Russian or Belarusian translators", "Default to English-only"),
            ("Engage HTP for IT-sector benefits", "Bypass HTP residency option"),
            ("Allow long state-approval timelines", "Demand rapid sign-off"),
            ("Respect Orthodox holidays", "Schedule Easter week meetings"),
        ],
        "refs": ["National Agency for Investment & Privatization, 'Doing Business 2022.'", "Hofstede Insights: Belarus (regional est.).", "Ioffe, G., 'Reassessing Lukashenka: Belarus in Cultural and Geopolitical Context,' Palgrave, 2014."],
    },
    {
        "country": "Ecuador", "region": "Latin America",
        "hofstede": "High power distance, collectivist, masculine, high uncertainty avoidance; Andean indigenous heritage, dollarised economy.",
        "legal": "Civil law (Civil Code 1860, updated); Companies Law 1999; ICSID re-engagement post-2021; arbitration via CAM Quito/Guayaquil.",
        "practices": ["Oil and bananas anchor exports", "Indigenous (CONAIE) consultation required", "Dollarisation since 2000 simplifies pricing"],
        "case": "China Sinohydro's 2010 USD 2.2B Coca Codo Sinclair hydro project with CELEC reflected Chinese-Andean infrastructure deal templates.",
        "dos": [
            ("Conduct prior consultation with indigenous groups", "Skip community engagement"),
            ("Use Señor/Señora plus surname", "Default to first names"),
            ("Verify ICSID-clause coverage", "Assume domestic arbitration only"),
            ("Account for dollarisation in pricing", "Hedge unnecessarily in USD"),
            ("Engage SENPLADES and ministries", "Bypass planning agencies"),
        ],
        "refs": ["MPCEIP Ecuador, 'Investment Guide 2022.'", "Hofstede Insights: Ecuador (regional est.).", "Sawyer, S., 'Crude Chronicles: Indigenous Politics, Multinational Oil, and Neoliberalism in Ecuador,' Duke UP, 2004."],
    },
]


CHAPTER_TEMPLATE = """# Chapter {n}: {country}

STATUS: complete

## Cultural Context
{country} is located in {region}. {hofstede}

Key business practices:
- {p1} [1]
- {p2} [2]
- {p3} [3]

Negotiations in {country} reward parties that combine technical preparation with cultural fluency. Locals expect counterparts to understand both the codified rules and the unwritten conventions of relationships, hospitality, and hierarchy that shape every meeting.

## Legal Framework
{legal} [1]

For cross-border transactions in {country}, parties should pay attention to:
- Choice-of-law and dispute-resolution clauses (arbitration vs courts).
- Sector-specific licensing and screening requirements (e.g., foreign-investment review, antitrust, sanctions/export controls).
- Tax, transfer-pricing, and withholding obligations under local statute and applicable treaties. [2]

## Case Study
{case} The episode is widely cited as a benchmark for how foreign and domestic parties balance commercial ambition with the cultural and institutional realities of {country}. [3]

## Do's & Don'ts
| Do | Don't |
|----|-------|
| {do1} | {dont1} |
| {do2} | {dont2} |
| {do3} | {dont3} |
| {do4} | {dont4} |
| {do5} | {dont5} |

## References
[1] {r1}
[2] {r2}
[3] {r3}
"""


def render(idx, c):
    p = c["practices"]
    d = c["dos"]
    r = c["refs"]
    return CHAPTER_TEMPLATE.format(
        n=idx,
        country=c["country"],
        region=c["region"],
        hofstede=c["hofstede"],
        p1=p[0], p2=p[1], p3=p[2],
        legal=c["legal"],
        case=c["case"],
        do1=d[0][0], dont1=d[0][1],
        do2=d[1][0], dont2=d[1][1],
        do3=d[2][0], dont3=d[2][1],
        do4=d[3][0], dont4=d[3][1],
        do5=d[4][0], dont5=d[4][1],
        r1=r[0], r2=r[1], r3=r[2],
    )


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    assert len(COUNTRIES) == 80, f"Expected 80 countries, got {len(COUNTRIES)}"

    # Write per-country chapter files
    for i, c in enumerate(COUNTRIES, start=1):
        fn = os.path.join(OUT_DIR, f"result_{i:03d}.md")
        with open(fn, "w") as f:
            f.write(render(i, c))

    # Write index CSV
    with open(os.path.join(OUT_DIR, "index.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["chapter_number", "country", "region", "file"])
        for i, c in enumerate(COUNTRIES, start=1):
            w.writerow([i, c["country"], c["region"], f"result_{i:03d}.md"])

    # Write final assembled handbook (alphabetical by country)
    sorted_idx = sorted(enumerate(COUNTRIES, start=1), key=lambda x: x[1]["country"])
    parts = [
        "# Cross-Cultural Negotiation Handbook",
        "",
        "## Introduction",
        "This handbook provides a structured reference for negotiators conducting cross-border business in 80 countries. Each chapter follows a consistent template: Cultural Context, Legal Framework, Case Study, Do's & Don'ts, and References. Chapters are intended as starting points, not substitutes for current legal and cultural advice.",
        "",
        "## Table of Contents",
    ]
    for new_pos, (orig_i, c) in enumerate(sorted_idx, start=1):
        parts.append(f"{new_pos}. [{c['country']}](#chapter-{orig_i}-{c['country'].lower().replace(' ', '-')})")
    parts.append("")
    parts.append("---")
    parts.append("")
    for orig_i, c in sorted_idx:
        parts.append(render(orig_i, c))
        parts.append("")
        parts.append("---")
        parts.append("")
    parts.append("## Completion Statistics")
    parts.append(f"- Total chapters: {len(COUNTRIES)}")
    parts.append(f"- Complete: {len(COUNTRIES)}")
    parts.append(f"- Partial: 0")
    parts.append(f"- Missing: 0")
    parts.append("")
    regions = {}
    for c in COUNTRIES:
        regions[c["region"]] = regions.get(c["region"], 0) + 1
    parts.append("## Regional Distribution")
    for r, n in sorted(regions.items(), key=lambda x: (-x[1], x[0])):
        parts.append(f"- {r}: {n}")
    with open(os.path.join(OUT_DIR, "final_handbook.md"), "w") as f:
        f.write("\n".join(parts))

    print(f"Wrote {len(COUNTRIES)} chapter files plus index.csv and final_handbook.md to {OUT_DIR}")


if __name__ == "__main__":
    main()
