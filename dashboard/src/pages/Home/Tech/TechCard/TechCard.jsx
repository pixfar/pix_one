import React from 'react';

const TechCard = ({ image, title, alt = title }) => {
    return (
        <div className="flex flex-col items-center gap-4 pt-10">
            {/* Circular background with image */}
            <div className="flex h-40 w-40 items-center justify-center rounded-full bg-gray-300">
                <div className="relative h-32 w-32 rounded-xl overflow-hidden">
                    <img 
                        src={image || "/placeholder.svg"} 
                        alt={alt} 
                        className="object-contain absolute inset-0 h-full w-full"
                    />
                </div>
            </div>

            {/* Title */}
            <h3 className="text-center text-lg font-semibold ">{title}</h3>
        </div>
    );
};

export default TechCard;