import React from 'react';
import { Doctor } from '../types';

interface DoctorCardProps {
  doctor: Doctor;
  onSelect: (doctor: Doctor) => void;
}

const DoctorCard: React.FC<DoctorCardProps> = ({ doctor, onSelect }) => {
  // Clean up doctor name to remove duplicate "Dr." prefixes
  const cleanDoctorName = doctor.name.replace(/^Dr\.\s+Dr\.\s+/, 'Dr. ');
  const displayName = cleanDoctorName.startsWith('Dr.') ? cleanDoctorName : `Dr. ${cleanDoctorName}`;

  return (
    <div className="bg-chat-assistant border border-chat-border rounded-lg p-3 hover:bg-gray-700 transition-all duration-200 h-full">
      <div className="flex flex-col h-full">
        {/* Header with Avatar and Basic Info */}
        <div className="flex items-center space-x-3 mb-2">
          <div className="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
            <i className="fas fa-user-md text-white text-sm"></i>
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-white truncate">{displayName}</h3>
            <p className="text-blue-400 text-xs font-medium truncate">{doctor.specialization}</p>
          </div>
          <div className="flex items-center space-x-2">
            {doctor.rating && (
              <div className="flex items-center space-x-1 text-yellow-400">
                <i className="fas fa-star text-xs"></i>
                <span className="text-xs font-medium">{doctor.rating}</span>
              </div>
            )}
            {/* Calendar sync indicator - assuming this info comes from backend */}
            <div className="flex items-center space-x-1">
              <i className="fas fa-calendar text-green-500 text-xs" title="Calendar sync enabled"></i>
            </div>
          </div>
        </div>

        {/* Reason for recommendation */}
        <p className="text-gray-300 text-xs mb-2 leading-relaxed line-clamp-2">
          {doctor.reason}
        </p>

        {/* Experience and Details */}
        <div className="space-y-1 mb-2 flex-1">
          <div className="flex items-center space-x-2 text-gray-400 text-xs">
            <i className="fas fa-briefcase w-3"></i>
            <span className="truncate">{doctor.experience}</span>
          </div>
          {doctor.location && (
            <div className="flex items-center space-x-2 text-gray-400 text-xs">
              <i className="fas fa-map-marker-alt w-3"></i>
              <span className="truncate">{doctor.location}</span>
            </div>
          )}
          {doctor.availability && (
            <div className="flex items-center space-x-2 text-green-400 text-xs">
              <i className="fas fa-clock w-3"></i>
              <span className="truncate">{doctor.availability}</span>
            </div>
          )}
        </div>

        {/* Expertise Tags - Limited to 2 */}
        {doctor.expertise && doctor.expertise.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {doctor.expertise.slice(0, 2).map((tag, index) => (
              <span
                key={index}
                className="bg-blue-900 text-blue-300 text-xs px-2 py-1 rounded-full truncate"
              >
                {tag}
              </span>
            ))}
            {doctor.expertise.length > 2 && (
              <span className="text-gray-400 text-xs px-1">
                +{doctor.expertise.length - 2}
              </span>
            )}
          </div>
        )}

        {/* Select Button */}
        <button
          onClick={() => onSelect(doctor)}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-3 rounded-md transition-colors duration-200 flex items-center justify-center space-x-2 text-sm"
        >
          <i className="fas fa-calendar-check text-xs"></i>
          <span>Book Appointment</span>
        </button>
      </div>
    </div>
  );
};

export default DoctorCard; 