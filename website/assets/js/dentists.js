// Sample dentist data for Christchurch
const dentists = [
    {
        name: "Merivale Dental Group",
        slug: "merivale-dental-group",
        suburb: "Merivale",
        address: "42 Papanui Road, Merivale, Christchurch 8014",
        phone: "(03) 355 7890",
        email: "info@merivaledental.co.nz",
        website: "https://merivaledental.co.nz",
        rating: 4.9,
        reviewCount: 127,
        services: ["General Dentistry", "Cosmetic", "Teeth Whitening", "Implants", "Orthodontics"],
        pricing: [
            { service: "General Checkup & Clean", price: "$149" },
            { service: "Dental X-Ray", price: "$65" },
            { service: "Filling (Composite)", price: "$195 – $350" },
            { service: "Teeth Whitening", price: "$450" },
            { service: "Crown (Porcelain)", price: "$1,500 – $1,850" },
            { service: "Root Canal", price: "$850 – $1,200" },
            { service: "Dental Implant (Single)", price: "$4,200 – $5,500" },
            { service: "Orthodontic Consultation", price: "Free" }
        ],
        description: "A modern, family-friendly dental practice in the heart of Merivale offering comprehensive dental care with a gentle approach. Our experienced team uses the latest technology to ensure comfortable and effective treatments.",
        hours: {
            Monday: "8:00 AM – 5:30 PM",
            Tuesday: "8:00 AM – 5:30 PM",
            Wednesday: "8:00 AM – 7:00 PM",
            Thursday: "8:00 AM – 5:30 PM",
            Friday: "8:00 AM – 4:00 PM",
            Saturday: "9:00 AM – 1:00 PM",
            Sunday: "Closed"
        },
        reviews: [
            { name: "Sarah M.", rating: 5, date: "February 2026", text: "Absolutely wonderful experience. The team made me feel at ease from the moment I walked in. My teeth have never looked better!" },
            { name: "James T.", rating: 5, date: "January 2026", text: "Professional, friendly, and thorough. Dr. Chen took the time to explain everything clearly. Highly recommend for families." },
            { name: "Emma L.", rating: 4, date: "December 2025", text: "Great service and a lovely modern clinic. Parking can be a bit tricky but the care more than makes up for it." }
        ]
    },
    {
        name: "Riccarton Smiles Dental",
        slug: "riccarton-smiles-dental",
        suburb: "Riccarton",
        address: "118 Riccarton Road, Riccarton, Christchurch 8041",
        phone: "(03) 341 2233",
        email: "hello@riccartonsmiles.co.nz",
        website: "https://riccartonsmiles.co.nz",
        rating: 4.7,
        reviewCount: 89,
        services: ["General Dentistry", "Emergency", "Teeth Whitening", "Cosmetic"],
        pricing: [
            { service: "General Checkup & Clean", price: "$125" },
            { service: "Dental X-Ray", price: "$55" },
            { service: "Filling (Composite)", price: "$170 – $310" },
            { service: "Emergency Appointment", price: "$95" },
            { service: "Teeth Whitening", price: "$395" },
            { service: "Tooth Extraction (Simple)", price: "$180 – $250" },
            { service: "Crown (Porcelain)", price: "$1,350 – $1,700" }
        ],
        description: "Conveniently located near Westfield Riccarton, we provide quality dental care for the whole family. Same-day emergency appointments available. ACC registered provider.",
        hours: {
            Monday: "7:30 AM – 5:00 PM",
            Tuesday: "7:30 AM – 5:00 PM",
            Wednesday: "7:30 AM – 5:00 PM",
            Thursday: "7:30 AM – 7:00 PM",
            Friday: "7:30 AM – 4:30 PM",
            Saturday: "Closed",
            Sunday: "Closed"
        },
        reviews: [
            { name: "David K.", rating: 5, date: "March 2026", text: "Got an emergency appointment within an hour of calling. They fixed my chipped tooth perfectly. So grateful!" },
            { name: "Priya S.", rating: 4, date: "February 2026", text: "Friendly staff and quick service. The waiting room is comfortable and the prices are fair." },
            { name: "Tom W.", rating: 5, date: "January 2026", text: "Been going here for two years now. Consistent, quality dental care every time." }
        ]
    },
    {
        name: "Fendalton Dental Care",
        slug: "fendalton-dental-care",
        suburb: "Fendalton",
        address: "7 Memorial Avenue, Fendalton, Christchurch 8053",
        phone: "(03) 351 9988",
        email: "enquiries@fendaltondental.co.nz",
        website: "https://fendaltondental.co.nz",
        rating: 4.8,
        reviewCount: 156,
        services: ["General Dentistry", "Cosmetic", "Implants", "Orthodontics", "Teeth Whitening"],
        pricing: [
            { service: "General Checkup & Clean", price: "$175" },
            { service: "Dental X-Ray", price: "$75" },
            { service: "Filling (Composite)", price: "$220 – $380" },
            { service: "Teeth Whitening (In-Chair)", price: "$595" },
            { service: "Porcelain Veneer", price: "$1,600 – $2,100" },
            { service: "Crown (Porcelain)", price: "$1,750 – $2,100" },
            { service: "Dental Implant (Single)", price: "$4,800 – $6,200" },
            { service: "Invisalign", price: "$5,500 – $8,500" }
        ],
        description: "Premium dental practice offering personalised care with attention to detail. Specialising in cosmetic dentistry and dental implants. State-of-the-art facilities with a calming environment.",
        hours: {
            Monday: "8:30 AM – 5:00 PM",
            Tuesday: "8:30 AM – 5:00 PM",
            Wednesday: "8:30 AM – 5:00 PM",
            Thursday: "8:30 AM – 5:00 PM",
            Friday: "8:30 AM – 3:00 PM",
            Saturday: "By appointment",
            Sunday: "Closed"
        },
        reviews: [
            { name: "Catherine R.", rating: 5, date: "March 2026", text: "The best dental practice I've been to. They genuinely care about their patients and offer luxury-level service." },
            { name: "Michael B.", rating: 5, date: "February 2026", text: "Had two implants done here. The results are incredible — look and feel like natural teeth." },
            { name: "Lisa P.", rating: 4, date: "January 2026", text: "Beautiful clinic, very professional team. A bit pricey but the quality is worth it." }
        ]
    },
    {
        name: "CBD Dental Christchurch",
        slug: "cbd-dental-christchurch",
        suburb: "CBD",
        address: "Level 2, 56 Cashel Street, Christchurch Central 8011",
        phone: "(03) 379 4455",
        email: "appointments@cbddental.co.nz",
        website: "https://cbddental.co.nz",
        rating: 4.5,
        reviewCount: 72,
        services: ["General Dentistry", "Emergency", "Cosmetic", "Teeth Whitening"],
        pricing: [
            { service: "General Checkup & Clean", price: "$135" },
            { service: "Dental X-Ray", price: "$60" },
            { service: "Filling (Composite)", price: "$180 – $320" },
            { service: "Emergency Appointment", price: "$85" },
            { service: "Teeth Whitening", price: "$420" },
            { service: "Root Canal", price: "$800 – $1,100" },
            { service: "Crown (Porcelain)", price: "$1,400 – $1,750" }
        ],
        description: "Central city dental practice perfect for busy professionals. Quick checkups during your lunch break, with late evening appointments available on Wednesdays.",
        hours: {
            Monday: "7:00 AM – 6:00 PM",
            Tuesday: "7:00 AM – 6:00 PM",
            Wednesday: "7:00 AM – 8:00 PM",
            Thursday: "7:00 AM – 6:00 PM",
            Friday: "7:00 AM – 5:00 PM",
            Saturday: "Closed",
            Sunday: "Closed"
        },
        reviews: [
            { name: "Alex H.", rating: 5, date: "February 2026", text: "Love being able to pop in during lunch. Super efficient and professional team." },
            { name: "Jenny F.", rating: 4, date: "January 2026", text: "Great location in the CBD. Modern equipment and friendly dentists." }
        ]
    },
    {
        name: "Addington Family Dental",
        slug: "addington-family-dental",
        suburb: "Addington",
        address: "321 Lincoln Road, Addington, Christchurch 8024",
        phone: "(03) 338 5566",
        email: "care@addingtondental.co.nz",
        website: "https://addingtondental.co.nz",
        rating: 4.6,
        reviewCount: 95,
        services: ["General Dentistry", "Emergency", "Orthodontics", "Cosmetic"],
        pricing: [
            { service: "General Checkup & Clean", price: "$115" },
            { service: "Dental X-Ray", price: "$50" },
            { service: "Filling (Composite)", price: "$160 – $290" },
            { service: "Emergency Appointment", price: "$80" },
            { service: "Tooth Extraction (Simple)", price: "$160 – $220" },
            { service: "Braces (Metal)", price: "$4,500 – $6,500" },
            { service: "Crown (Porcelain)", price: "$1,300 – $1,650" }
        ],
        description: "Family-owned practice with over 20 years of serving the Addington community. We treat patients of all ages with warmth and expertise. Free parking available on-site.",
        hours: {
            Monday: "8:00 AM – 5:00 PM",
            Tuesday: "8:00 AM – 5:00 PM",
            Wednesday: "8:00 AM – 5:00 PM",
            Thursday: "8:00 AM – 5:00 PM",
            Friday: "8:00 AM – 4:00 PM",
            Saturday: "9:00 AM – 12:00 PM",
            Sunday: "Closed"
        },
        reviews: [
            { name: "Karen D.", rating: 5, date: "March 2026", text: "Our whole family goes here. The children love Dr. Patel — she's so patient and kind with the little ones." },
            { name: "Mark S.", rating: 4, date: "February 2026", text: "Reliable and affordable. Been a patient for over five years." },
            { name: "Natalie G.", rating: 5, date: "January 2026", text: "Friendly, no-pressure environment. They actually listen to your concerns." }
        ]
    },
    {
        name: "Halswell Dental Centre",
        slug: "halswell-dental-centre",
        suburb: "Halswell",
        address: "45 Halswell Road, Halswell, Christchurch 8025",
        phone: "(03) 322 7788",
        email: "info@halswelldental.co.nz",
        website: "https://halswelldental.co.nz",
        rating: 4.4,
        reviewCount: 61,
        services: ["General Dentistry", "Teeth Whitening", "Emergency"],
        pricing: [
            { service: "General Checkup & Clean", price: "$110" },
            { service: "Dental X-Ray", price: "$45" },
            { service: "Filling (Composite)", price: "$150 – $280" },
            { service: "Teeth Whitening", price: "$350" },
            { service: "Emergency Appointment", price: "$75" },
            { service: "Tooth Extraction (Simple)", price: "$150 – $210" }
        ],
        description: "Neighbourhood dental practice focused on preventive care and patient education. We believe in building long-term relationships with our patients and their families.",
        hours: {
            Monday: "8:30 AM – 5:00 PM",
            Tuesday: "8:30 AM – 5:00 PM",
            Wednesday: "8:30 AM – 5:00 PM",
            Thursday: "8:30 AM – 5:00 PM",
            Friday: "8:30 AM – 3:30 PM",
            Saturday: "Closed",
            Sunday: "Closed"
        },
        reviews: [
            { name: "Brian T.", rating: 4, date: "February 2026", text: "Good local dentist. Not the fanciest clinic but the care is excellent." },
            { name: "Sandra W.", rating: 5, date: "January 2026", text: "They take the time to explain everything properly. Great preventive care." }
        ]
    },
    {
        name: "Papanui Dental Studio",
        slug: "papanui-dental-studio",
        suburb: "Papanui",
        address: "29 Main North Road, Papanui, Christchurch 8053",
        phone: "(03) 352 4411",
        email: "studio@papanuidental.co.nz",
        website: "https://papanuidental.co.nz",
        rating: 4.8,
        reviewCount: 143,
        services: ["General Dentistry", "Cosmetic", "Implants", "Teeth Whitening", "Orthodontics"],
        pricing: [
            { service: "General Checkup & Clean", price: "$165" },
            { service: "Dental X-Ray", price: "$70" },
            { service: "Filling (Composite)", price: "$200 – $360" },
            { service: "Teeth Whitening (In-Chair)", price: "$550" },
            { service: "Porcelain Veneer", price: "$1,500 – $1,950" },
            { service: "Crown (Porcelain)", price: "$1,600 – $1,950" },
            { service: "Dental Implant (Single)", price: "$4,500 – $5,800" },
            { service: "Invisalign", price: "$5,000 – $8,000" }
        ],
        description: "Boutique dental studio combining artistry with dental science. Specialising in smile makeovers and cosmetic dentistry using the latest digital technology.",
        hours: {
            Monday: "8:00 AM – 5:30 PM",
            Tuesday: "8:00 AM – 5:30 PM",
            Wednesday: "8:00 AM – 6:30 PM",
            Thursday: "8:00 AM – 5:30 PM",
            Friday: "8:00 AM – 4:00 PM",
            Saturday: "9:00 AM – 2:00 PM",
            Sunday: "Closed"
        },
        reviews: [
            { name: "Rachel H.", rating: 5, date: "March 2026", text: "My smile transformation has been life-changing. The attention to detail here is unmatched." },
            { name: "Daniel C.", rating: 5, date: "February 2026", text: "Beautiful studio, lovely team, and incredible results. Worth every penny." },
            { name: "Sophie M.", rating: 4, date: "December 2025", text: "Excellent cosmetic work. The only reason for 4 stars is the wait time for appointments can be a few weeks." }
        ]
    },
    {
        name: "Avonhead Dental Practice",
        slug: "avonhead-dental-practice",
        suburb: "Avonhead",
        address: "184 Withells Road, Avonhead, Christchurch 8042",
        phone: "(03) 358 9900",
        email: "book@avonheaddental.co.nz",
        website: "https://avonheaddental.co.nz",
        rating: 4.3,
        reviewCount: 54,
        services: ["General Dentistry", "Emergency", "Teeth Whitening"],
        pricing: [
            { service: "General Checkup & Clean", price: "$105" },
            { service: "Dental X-Ray", price: "$45" },
            { service: "Filling (Composite)", price: "$145 – $270" },
            { service: "Emergency Appointment", price: "$70" },
            { service: "Teeth Whitening", price: "$340" },
            { service: "Tooth Extraction (Simple)", price: "$145 – $200" },
            { service: "Root Canal", price: "$750 – $1,050" }
        ],
        description: "Affordable, quality dental care for the Avonhead community. We pride ourselves on being accessible and welcoming to everyone. Walk-ins welcome for emergencies.",
        hours: {
            Monday: "8:00 AM – 5:00 PM",
            Tuesday: "8:00 AM – 5:00 PM",
            Wednesday: "8:00 AM – 5:00 PM",
            Thursday: "8:00 AM – 5:00 PM",
            Friday: "8:00 AM – 4:00 PM",
            Saturday: "Closed",
            Sunday: "Closed"
        },
        reviews: [
            { name: "Peter J.", rating: 4, date: "February 2026", text: "Good value for money. Straightforward and honest about what treatment you actually need." },
            { name: "May L.", rating: 5, date: "January 2026", text: "Very welcoming to new patients. Felt comfortable immediately." }
        ]
    },
    {
        name: "Sumner Coastal Dental",
        slug: "sumner-coastal-dental",
        suburb: "Sumner",
        address: "12 Wakefield Avenue, Sumner, Christchurch 8081",
        phone: "(03) 326 7722",
        email: "hello@sumnercoastaldental.co.nz",
        website: "https://sumnercoastaldental.co.nz",
        rating: 4.7,
        reviewCount: 78,
        services: ["General Dentistry", "Cosmetic", "Teeth Whitening", "Implants"],
        pricing: [
            { service: "General Checkup & Clean", price: "$155" },
            { service: "Dental X-Ray", price: "$65" },
            { service: "Filling (Composite)", price: "$190 – $340" },
            { service: "Teeth Whitening (In-Chair)", price: "$495" },
            { service: "Porcelain Veneer", price: "$1,450 – $1,900" },
            { service: "Crown (Porcelain)", price: "$1,500 – $1,850" },
            { service: "Dental Implant (Single)", price: "$4,400 – $5,700" }
        ],
        description: "Relaxed coastal dental practice with ocean views from our treatment rooms. We combine a calming environment with high-quality dental care for a truly unique experience.",
        hours: {
            Monday: "9:00 AM – 5:00 PM",
            Tuesday: "9:00 AM – 5:00 PM",
            Wednesday: "9:00 AM – 5:00 PM",
            Thursday: "9:00 AM – 5:00 PM",
            Friday: "9:00 AM – 3:00 PM",
            Saturday: "Closed",
            Sunday: "Closed"
        },
        reviews: [
            { name: "Greg A.", rating: 5, date: "March 2026", text: "Most relaxing dental experience ever. The views help distract from any nerves!" },
            { name: "Nicole R.", rating: 5, date: "February 2026", text: "Beautiful clinic by the beach. The team are amazing — I actually enjoy going to the dentist now." },
            { name: "Tim B.", rating: 4, date: "January 2026", text: "Great practice but a bit of a drive if you're not local. Worth it though." }
        ]
    },
    {
        name: "Hornby Dental Surgery",
        slug: "hornby-dental-surgery",
        suburb: "Hornby",
        address: "8 Carmen Road, Hornby, Christchurch 8042",
        phone: "(03) 349 3311",
        email: "admin@hornbydental.co.nz",
        website: "https://hornbydental.co.nz",
        rating: 4.5,
        reviewCount: 67,
        services: ["General Dentistry", "Emergency", "Orthodontics", "Teeth Whitening"],
        pricing: [
            { service: "General Checkup & Clean", price: "$110" },
            { service: "Dental X-Ray", price: "$50" },
            { service: "Filling (Composite)", price: "$155 – $285" },
            { service: "Emergency Appointment", price: "$80" },
            { service: "Teeth Whitening", price: "$375" },
            { service: "Tooth Extraction (Simple)", price: "$155 – $215" },
            { service: "Braces (Metal)", price: "$4,200 – $6,200" }
        ],
        description: "Experienced dental team providing quality affordable care to the Hornby community and wider southwest Christchurch. Emergency tooth repair and extractions available daily.",
        hours: {
            Monday: "8:00 AM – 5:30 PM",
            Tuesday: "8:00 AM – 5:30 PM",
            Wednesday: "8:00 AM – 5:30 PM",
            Thursday: "8:00 AM – 5:30 PM",
            Friday: "8:00 AM – 4:30 PM",
            Saturday: "9:00 AM – 12:00 PM",
            Sunday: "Closed"
        },
        reviews: [
            { name: "Wayne P.", rating: 5, date: "February 2026", text: "Honest, reliable, and fairly priced. The best dentist I've found in the Hornby area." },
            { name: "Angela M.", rating: 4, date: "January 2026", text: "Good emergency service. Got seen quickly and the pain was resolved immediately." }
        ]
    }
];
