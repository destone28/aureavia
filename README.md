# AUREAVIA - NCC Driver Dashboard

Complete standalone web application for NCC (Noleggio Con Conducente) drivers to manage ride assignments.

## 🚗 Features

### Authentication
- ✅ Secure login with email/password validation
- ✅ Session persistence
- ✅ Protected routes with auto-redirect

### Rides Management
- ✅ View all assigned and available rides
- ✅ Filter by status (All/Available/Assigned)
- ✅ Filter by passengers, route type, and distance
- ✅ Accept or decline rides
- ✅ View detailed ride information
- ✅ Navigate to pickup location (Google Maps)
- ✅ Call passengers directly

### Driver Profile
- ✅ Personal information display
- ✅ Activity statistics (rides, earnings, distance)
- ✅ Recent activities history
- ✅ Security settings

### Vehicle Information
- ✅ Vehicle details (license plate, type, fuel)
- ✅ Capacity information
- ✅ NCC compliance status
- ✅ Documents & registration tracking

## 📁 File Structure

```
aureavia/
├── index.html              # Login page
├── rides-list.html         # Rides dashboard
├── ride-detail.html        # Individual ride details
├── profile.html            # Driver profile
├── vehicle.html            # Vehicle information
├── js/
│   ├── navigation.js       # Global navigation & utilities
│   └── styles.css          # Animations & global styles
├── README.md               # This file
└── NAVIGATION_GUIDE.md     # Detailed navigation documentation
```

## 🎨 Design System

### Colors
- **Primary Orange**: `#FF8C00`
- **Secondary Orange**: `#FFA500`
- **Dark Gray**: `#2D2D2D`
- **Medium Gray**: `#666666`
- **Light Gray**: `#F5F5F5`
- **Success Green**: `#4CAF50`
- **Error Red**: `#F44336`
- **Info Blue**: `#2196F3`

### Typography
- **Font Family**: Open Sans (400, 600, 700)
- **Headings**: 24-36px, Bold
- **Body**: 14-16px, Regular
- **Labels**: 12-14px, Medium

### Components
- **Cards**: White background, 12-16px border-radius, soft shadows
- **Buttons**: 12px border-radius, smooth hover transitions
- **Inputs**: 8-12px border-radius, focus states with orange accent
- **Badges**: Rounded pills with status colors
- **Toast Notifications**: Slide-in from right, auto-dismiss

## 🚀 Getting Started

### Local Development
1. Clone or download the repository
2. Open `index.html` in a web browser
3. Login with any email/password (min 6 chars for password)

### Login Credentials
- Any email format (e.g., `driver@example.com`)
- Any password with at least 6 characters

### Navigation
- **Dashboard**: View and filter rides
- **Ride Details**: Click "View Details" on any ride card
- **Profile**: Click user avatar → "Your Profile"
- **Vehicle**: Click user avatar → "Vehicle"
- **Logout**: Click user avatar → "Logout"

## 📱 Responsive Design

### Desktop (≥ 768px)
- Full navigation with dropdown menu
- Multi-column layouts
- Hover effects and transitions

### Mobile (< 768px)
- Hamburger menu with slide-in panel
- Stacked layouts
- Touch-friendly tap targets
- Optimized spacing

## ⌨️ Keyboard Navigation

- **Tab**: Navigate through interactive elements
- **Enter/Space**: Activate buttons and links
- **ESC**: Close modals and menus
- **Arrow Keys**: Navigate within menus

## ♿ Accessibility

- ✅ ARIA labels on icon-only buttons
- ✅ Semantic HTML structure
- ✅ Keyboard navigation support
- ✅ Focus visible states
- ✅ Screen reader compatible
- ✅ Sufficient color contrast

## 🎯 Key Interactions

### Login Flow
1. Enter email and password
2. Click "Login" button
3. Form validates inputs
4. Shows loading state
5. Redirects to rides dashboard

### Accept Ride Flow
1. Click "View Details" on a ride
2. Review ride information
3. Click "Accept Ride"
4. See success modal with animation
5. Options to navigate or call passenger

### Filter Rides
1. Click status tabs (All/Available/Assigned)
2. Toggle filter chips
3. Rides update in real-time
4. Multiple filters can be active

## 🔧 Technical Details

### Technologies
- **HTML5**: Semantic markup
- **CSS3**: Custom properties, animations, flexbox, grid
- **Vanilla JavaScript**: ES6+, no frameworks
- **LocalStorage**: Session persistence
- **SVG**: Scalable vector icons

### Browser Support
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile Safari iOS 14+
- Chrome Android 90+

### Performance
- Lightweight (~80KB total)
- No external dependencies
- Fast page loads
- Smooth 60fps animations
- Optimized DOM manipulation

## 📊 Mock Data

The application includes 6 sample rides with varied data:
1. Available - Milano Centrale → Malpensa (€85)
2. Available - Via Montenapoleone → Como (€120)
3. Assigned - Hotel Principe → Linate (€65)
4. Assigned - Bergamo Airport → Milano (€95)
5. Available - Porta Garibaldi → Torino (€180)
6. Available - Como Centro → Malpensa (€130)

## 🔐 Security Notes

- This is a **frontend-only prototype**
- Uses localStorage for demo purposes
- **Not production-ready** - requires backend integration
- No actual authentication server
- Mock data only

## 🛠️ Customization

### Change Colors
Edit color values in each HTML file's `<style>` section:
```css
/* Primary Orange */
#FF8C00 → your color

/* Gradients */
linear-gradient(135deg, #FF8C00 0%, #FFA500 100%)
```

### Add New Pages
1. Create new HTML file
2. Include navigation.js and styles.css
3. Add authentication check: `checkAuth()`
4. Add toast container: `<div id="toast-container"></div>`
5. Link from dropdown menu

### Modify Ride Data
Edit the `ridesData` object in `ride-detail.html`

## 📝 API Integration (Future)

To connect to a real backend:
1. Replace `localStorage` with API calls
2. Add authentication tokens
3. Fetch rides from `/api/rides`
4. POST to `/api/rides/:id/accept`
5. Handle errors with toast notifications

## 📄 License

This is a demo project created for AUREAVIA.

## 👨‍💻 Development

### File Modifications
All HTML files are standalone and can be edited independently.

Key files:
- `js/navigation.js` - All navigation and utility functions
- `js/styles.css` - Global animations and component styles

### Adding Features
1. Add function to `navigation.js`
2. Add styles to `styles.css`
3. Update HTML files to use new function
4. Test across all pages
5. Update NAVIGATION_GUIDE.md

## 🐛 Known Limitations

- No real backend integration
- Mock data only
- No data persistence across sessions
- No image uploads
- No real-time updates
- No push notifications

## 🎉 Credits

Design: AUREAVIA Figma mockups
Development: Standalone HTML/CSS/JS implementation
Icons: Feather Icons (SVG inline)
Fonts: Google Fonts (Open Sans)

---

**Last Updated**: December 2025
**Version**: 1.0.0